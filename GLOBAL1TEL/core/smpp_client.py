"""
Real SMPP v3.4 engine — pure Python, no third-party library.

Two directions are supported:

  SmppServer      — the panel acts as the SMSC. Carriers connect OUTBOUND to
                    us with the system_id/password from their SMPP Account and
                    push messages as submit_sm / deliver_sm.
  SmppConnection  — the panel acts as the ESME and binds OUTBOUND, transceiver
                    mode, to the carrier's SMSC. The carrier then pushes
                    deliver_sm PDUs down that same socket.

Both funnel every incoming message through the same on_message() callback,
which is wired to ingest_sms() so an OTP lands in the CDR either way.

PDUs implemented:
  bind_transceiver / transmitter / receiver  (+ responses)
  enquire_link / enquire_link_resp           (keepalive, both directions)
  deliver_sm / deliver_sm_resp               (incoming messages)
  submit_sm / submit_sm_resp                 (carriers that push this way)
  unbind / unbind_resp
  generic_nack                               (for anything unparseable, instead
                                              of silently dropping it)

MESSAGE DECODING — this is what makes OTPs actually readable. A parser that
decodes every message as UTF-8 and ignores the rest of the PDU only survives
plain ASCII. This one honours:
  * data_coding      — GSM 03.38, IA5/ASCII, Latin-1, UCS-2, plus the
                       message-class variants (0xF0-0xFF) carriers use.
  * esm_class UDH    — the 0x40 bit means a User Data Header is prepended to
                       short_message; those bytes are stripped instead of
                       being pasted onto the front of the OTP.
  * message_payload  — TLV 0x0424. Many carriers send sm_length=0 and put the
                       whole body in this optional field; that would otherwise
                       arrive as an empty message and the OTP would be lost.
  * concatenation    — multi-part messages (UDH IEI 0x00/0x08) are buffered
                       and reassembled, so a long OTP text is not split across
                       two half-rows in the CDR.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import struct
import time
from datetime import datetime, timezone

logger = logging.getLogger("smpp_client")


def _decode_password(stored: str) -> str:
    """The admin UI stores the password base64-encoded (so it is never shown
    in plaintext in the accounts list/API response). Decode it back to the
    real value the carrier actually expects for bind_transceiver."""
    if not stored:
        return ""
    try:
        return base64.b64decode(stored).decode("utf-8", errors="replace")
    except Exception:
        return stored  # already-plain password (e.g. entered directly via API)


# ─── SMPP v3.4 command IDs ───────────────────────────────────────────────────
CMD_BIND_RECEIVER = 0x00000001
CMD_BIND_RECEIVER_RESP = 0x80000001
CMD_BIND_TRANSMITTER = 0x00000002
CMD_BIND_TRANSMITTER_RESP = 0x80000002
CMD_BIND_TRANSCEIVER = 0x00000009
CMD_BIND_TRANSCEIVER_RESP = 0x80000009
CMD_ENQUIRE_LINK = 0x00000015
CMD_ENQUIRE_LINK_RESP = 0x80000015
CMD_DELIVER_SM = 0x00000005
CMD_DELIVER_SM_RESP = 0x80000005
CMD_UNBIND = 0x00000006
CMD_UNBIND_RESP = 0x80000006
CMD_GENERIC_NACK = 0x80000000
CMD_SUBMIT_SM = 0x00000004
CMD_SUBMIT_SM_RESP = 0x80000004

STATUS_OK = 0x00000000
STATUS_INVALID_SYSID = 0x0000000F
STATUS_INVALID_PASWD = 0x0000000E
STATUS_ALREADY_BOUND = 0x00000005

TLV_MESSAGE_PAYLOAD = 0x0424

# GSM 03.38 default alphabet (7-bit), unpacked one septet per octet — which is
# how SMPP carries it. Index = septet value.
_GSM7_BASIC = (
    "@\u00a3$\u00a5\u00e8\u00e9\u00f9\u00ec\u00f2\u00c7\n\u00d8\u00f8\r\u00c5\u00e5"
    "\u0394_\u03a6\u0393\u039b\u03a9\u03a0\u03a8\u03a3\u0398\u039e\x1b\u00c6\u00e6\u00df\u00c9"
    " !\"#\u00a4%&'()*+,-./"
    "0123456789:;<=>?"
    "\u00a1ABCDEFGHIJKLMNO"
    "PQRSTUVWXYZ\u00c4\u00d6\u00d1\u00dc\u00a7"
    "\u00bfabcdefghijklmno"
    "pqrstuvwxyz\u00e4\u00f6\u00f1\u00fc\u00e0"
)
_GSM7_EXT = {
    0x0A: "\n", 0x14: "^", 0x28: "{", 0x29: "}", 0x2F: "\\",
    0x3C: "[", 0x3D: "~", 0x3E: "]", 0x40: "|", 0x65: "\u20ac",
}


def _decode_gsm7(data: bytes) -> str:
    out = []
    escaped = False
    for byte in data:
        septet = byte & 0x7F
        if escaped:
            out.append(_GSM7_EXT.get(septet, " "))
            escaped = False
            continue
        if septet == 0x1B:
            escaped = True
            continue
        out.append(_GSM7_BASIC[septet] if septet < len(_GSM7_BASIC) else " ")
    return "".join(out)


def decode_message(data: bytes, data_coding: int = 0) -> str:
    """Turn short_message / message_payload bytes into readable text using the
    PDU's data_coding, instead of assuming UTF-8."""
    if not data:
        return ""
    coding = data_coding & 0xFF
    # 0xF0-0xFF: message-class marker; the alphabet lives in bit 2.
    if coding & 0xF0 == 0xF0:
        coding = 0x04 if (coding & 0x04) else 0x00

    try:
        if coding in (0x00, 0x10, 0x11, 0x12, 0x13):          # GSM 03.38 default
            text = _decode_gsm7(data)
            # Some carriers advertise data_coding 0 but actually send UTF-8.
            # Prefer UTF-8 when the GSM7 pass produced obvious junk.
            try:
                utf8 = data.decode("utf-8")
                if utf8.isprintable() and not text.isprintable():
                    return utf8
            except UnicodeDecodeError:
                pass
            return text
        if coding in (0x01, 0x05):                            # IA5 / ASCII
            return data.decode("ascii", errors="replace")
        if coding in (0x03, 0x07):                            # Latin-1 / ISO-8859-1
            return data.decode("latin-1", errors="replace")
        if coding in (0x08, 0x18, 0x19, 0x1A, 0x1B):          # UCS-2 / UTF-16BE
            if len(data) % 2:
                data = data[:-1]
            return data.decode("utf-16-be", errors="replace")
        if coding in (0x02, 0x04):                            # 8-bit binary
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1", errors="replace")
    except Exception as exc:
        logger.warning("decode_message failed (data_coding=%s): %s", hex(data_coding), exc)

    # Unknown coding — try the two encodings real traffic actually uses.
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1", errors="replace")


def parse_udh(data: bytes):
    """Split a User Data Header off the front of the message body.

    Returns (payload_without_udh, concat_info) where concat_info is
    {'ref': int, 'total': int, 'seq': int} for a multi-part message, else None.
    """
    if not data:
        return data, None
    udh_len = data[0]
    if udh_len + 1 > len(data):
        return data, None
    udh = data[1:1 + udh_len]
    payload = data[1 + udh_len:]

    concat = None
    i = 0
    while i + 1 < len(udh):
        iei = udh[i]
        ie_len = udh[i + 1]
        value = udh[i + 2:i + 2 + ie_len]
        if iei == 0x00 and len(value) >= 3:            # 8-bit concat reference
            concat = {"ref": value[0], "total": value[1], "seq": value[2]}
        elif iei == 0x08 and len(value) >= 4:          # 16-bit concat reference
            concat = {"ref": (value[0] << 8) | value[1], "total": value[2], "seq": value[3]}
        i += 2 + ie_len
    return payload, concat


def parse_tlvs(data: bytes) -> dict:
    """Parse the optional-parameter section that follows short_message."""
    tlvs: dict = {}
    offset = 0
    while offset + 4 <= len(data):
        tag, length = struct.unpack(">HH", data[offset:offset + 4])
        offset += 4
        if length > len(data) - offset:
            break
        tlvs[tag] = data[offset:offset + length]
        offset += length
    return tlvs


def _cstr(s: str) -> bytes:
    """C-octet string: value + null terminator."""
    return (s or "").encode("ascii", errors="replace") + b"\x00"


def _read_cstr(buf: bytes, offset: int):
    """Read a null-terminated string starting at offset. Returns (value, new_offset)."""
    end = buf.find(b"\x00", offset)
    if end == -1:
        return "", len(buf)
    return buf[offset:end].decode("ascii", errors="replace"), end + 1


def encode_pdu(command_id: int, command_status: int, sequence_number: int, body: bytes = b"") -> bytes:
    header = struct.pack(">IIII", 16 + len(body), command_id, command_status, sequence_number)
    return header + body


def decode_header(data: bytes):
    return struct.unpack(">IIII", data[:16])


def build_bind_transceiver(system_id: str, password: str, sequence_number: int) -> bytes:
    body = (
        _cstr(system_id)
        + _cstr(password)
        + _cstr("")           # system_type
        + bytes([0x34])       # interface_version — SMPP v3.4
        + bytes([0x00])       # addr_ton
        + bytes([0x00])       # addr_npi
        + _cstr("")           # address_range
    )
    return encode_pdu(CMD_BIND_TRANSCEIVER, STATUS_OK, sequence_number, body)


def build_enquire_link(sequence_number: int) -> bytes:
    return encode_pdu(CMD_ENQUIRE_LINK, STATUS_OK, sequence_number, b"")


def build_enquire_link_resp(sequence_number: int) -> bytes:
    return encode_pdu(CMD_ENQUIRE_LINK_RESP, STATUS_OK, sequence_number, b"")


def build_bind_resp(command_id: int, status: int, sequence_number: int, system_id: str = "") -> bytes:
    """Generic bind_*_resp builder — command_id must be the matching *_RESP id
    for whichever bind type the client requested (TRX/TX/RX)."""
    return encode_pdu(command_id, status, sequence_number, _cstr(system_id))


def build_submit_sm_resp(sequence_number: int, message_id: str = "") -> bytes:
    return encode_pdu(CMD_SUBMIT_SM_RESP, STATUS_OK, sequence_number, _cstr(message_id))


def build_deliver_sm_resp(sequence_number: int, message_id: str = "") -> bytes:
    return encode_pdu(CMD_DELIVER_SM_RESP, STATUS_OK, sequence_number, _cstr(message_id))


def build_unbind(sequence_number: int) -> bytes:
    return encode_pdu(CMD_UNBIND, STATUS_OK, sequence_number, b"")


def build_generic_nack(sequence_number: int, status: int = 0x00000003) -> bytes:
    return encode_pdu(CMD_GENERIC_NACK, status, sequence_number, b"")


class _ConcatBuffer:
    """Holds the parts of split messages until every segment has arrived.
    Incomplete sets are dropped after TTL so a lost segment cannot leak memory."""

    TTL = 300  # seconds

    def __init__(self):
        self._parts: dict = {}

    def add(self, key, concat, text: str):
        now = time.time()
        self._expire(now)
        entry = self._parts.setdefault(key, {"total": concat["total"], "segments": {}, "ts": now})
        entry["ts"] = now
        entry["segments"][concat["seq"]] = text
        if len(entry["segments"]) >= entry["total"]:
            self._parts.pop(key, None)
            return "".join(entry["segments"][i] for i in sorted(entry["segments"]))
        return None

    def _expire(self, now: float):
        for key in [k for k, v in self._parts.items() if now - v["ts"] > self.TTL]:
            self._parts.pop(key, None)


def parse_deliver_sm(body: bytes) -> dict:
    """Parse the fields we need: source_addr (CLI/from), destination_addr (the
    number the SMS was sent to), and the message body — correctly decoded.

    Returns {'from','to','message','data_coding','concat','is_delivery_receipt'}.
    """
    offset = 0
    service_type, offset = _read_cstr(body, offset)
    offset += 2  # source_addr_ton, source_addr_npi
    source_addr, offset = _read_cstr(body, offset)
    offset += 2  # dest_addr_ton, dest_addr_npi
    destination_addr, offset = _read_cstr(body, offset)

    esm_class = body[offset] if offset < len(body) else 0
    offset += 1
    offset += 1  # protocol_id
    offset += 1  # priority_flag
    _, offset = _read_cstr(body, offset)  # schedule_delivery_time
    _, offset = _read_cstr(body, offset)  # validity_period
    offset += 1  # registered_delivery
    offset += 1  # replace_if_present_flag
    data_coding = body[offset] if offset < len(body) else 0
    offset += 1
    offset += 1  # sm_default_msg_id

    sm_length = body[offset] if offset < len(body) else 0
    offset += 1
    raw = body[offset:offset + sm_length] if sm_length else b""
    offset += sm_length

    # Everything after short_message is the optional-parameter (TLV) section.
    tlvs = parse_tlvs(body[offset:]) if offset < len(body) else {}

    # Carriers that send sm_length=0 put the whole body in message_payload.
    if not raw and TLV_MESSAGE_PAYLOAD in tlvs:
        raw = tlvs[TLV_MESSAGE_PAYLOAD]

    concat = None
    if esm_class & 0x40:  # UDH present
        raw, concat = parse_udh(raw)

    message = decode_message(raw, data_coding)

    return {
        "from": source_addr,
        "to": destination_addr,
        "message": message,
        "data_coding": data_coding,
        "esm_class": esm_class,
        "concat": concat,
        "service_type": service_type,
        # esm_class message-type bits mark an SMSC delivery receipt rather than
        # a real inbound SMS, so callers can keep receipts out of the OTP feed.
        "is_delivery_receipt": (esm_class & 0x3C) in (0x04, 0x20) and (esm_class & 0x3C) != 0,
    }


# submit_sm has the exact same body layout as deliver_sm in SMPP v3.4
parse_sm_pdu = parse_deliver_sm


class SmppConnection:
    """One persistent bind to one carrier account. Auto-reconnects forever
    with capped exponential backoff until explicitly stopped."""

    def __init__(self, account: dict, on_message, on_status_change):
        self.account = account
        self.on_message = on_message               # async fn(from, to, message, sms_id, company)
        self.on_status_change = on_status_change   # async fn(account_id, status)
        self._stop = False
        self._seq = 0
        self._reader = None
        self._writer = None
        self._task = None
        self._keepalive_task = None
        self._write_lock = asyncio.Lock()
        self._concat = _ConcatBuffer()

    def next_seq(self) -> int:
        self._seq += 1
        if self._seq > 0x7FFFFFFF:
            self._seq = 1
        return self._seq

    def start(self):
        self._task = asyncio.create_task(self._run_forever())
        return self._task

    async def _send(self, pdu: bytes):
        """All writes go through here, serialized by a lock, so the keepalive
        loop and the message-response loop can never interleave bytes on the
        wire — that byte-level collision silently corrupts the PDU stream and
        makes the carrier drop the connection."""
        async with self._write_lock:
            self._writer.write(pdu)
            await self._writer.drain()

    async def stop(self):
        self._stop = True
        if self._writer:
            try:
                await self._send(build_unbind(self.next_seq()))
            except Exception:
                pass
            try:
                self._writer.close()
            except Exception:
                pass
        if self._keepalive_task:
            self._keepalive_task.cancel()
        if self._task:
            self._task.cancel()

    async def _run_forever(self):
        backoff = 3
        while not self._stop:
            try:
                await self._connect_and_bind()
                await self._read_loop()
                backoff = 3  # reset after a clean session
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("SMPP [%s] connection error: %s", self.account.get("company"), exc)
                await self.on_status_change(self.account["id"], "error")
            if self._stop:
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 60)

    async def _connect_and_bind(self):
        host = self.account["host"]
        port = int(self.account["port"])
        system_id = self.account.get("system_id", "")
        password = _decode_password(self.account.get("password", ""))

        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=15
        )

        await self._send(build_bind_transceiver(system_id, password, self.next_seq()))

        header_bytes = await asyncio.wait_for(self._reader.readexactly(16), timeout=15)
        command_length, command_id, command_status, sequence_number = decode_header(header_bytes)
        if command_length > 16:
            await self._reader.readexactly(command_length - 16)

        if command_id != CMD_BIND_TRANSCEIVER_RESP or command_status != STATUS_OK:
            raise ConnectionError(f"Bind rejected (status={command_status})")

        await self.on_status_change(self.account["id"], "active")
        logger.info("SMPP [%s] bound to %s:%s", self.account.get("company"), host, port)

        self._keepalive_task = asyncio.create_task(self._keepalive_loop())

    async def _keepalive_loop(self):
        try:
            while not self._stop and self._writer and not self._writer.is_closing():
                await asyncio.sleep(30)
                await self._send(build_enquire_link(self.next_seq()))
        except Exception:
            pass

    async def _handle_incoming(self, msg: dict, sequence_number: int):
        """Reassemble multi-part messages, skip delivery receipts, then ingest."""
        if msg.get("is_delivery_receipt"):
            return
        text = msg["message"]
        if msg.get("concat"):
            key = (self.account["id"], msg["from"], msg["to"], msg["concat"]["ref"])
            text = self._concat.add(key, msg["concat"], text)
            if text is None:
                return  # still waiting for the remaining segments
        stamp = int(datetime.now(timezone.utc).timestamp())
        sms_id = f"smpp-{self.account['id']}-{sequence_number}-{stamp}"
        await self.on_message(
            msg["from"], msg["to"], text, sms_id,
            self.account.get("company", self.account.get("system_id", "")),
        )

    async def _read_loop(self):
        try:
            while not self._stop:
                header_bytes = await asyncio.wait_for(self._reader.readexactly(16), timeout=90)
                command_length, command_id, command_status, sequence_number = decode_header(header_bytes)
                body = await self._reader.readexactly(command_length - 16) if command_length > 16 else b""

                if command_id == CMD_DELIVER_SM:
                    try:
                        msg = parse_deliver_sm(body)
                        await self._handle_incoming(msg, sequence_number)
                        await self._send(build_deliver_sm_resp(sequence_number))
                    except Exception as exc:
                        logger.warning("SMPP deliver_sm parse error: %s", exc)
                        await self._send(build_generic_nack(sequence_number))

                elif command_id == CMD_ENQUIRE_LINK:
                    await self._send(build_enquire_link_resp(sequence_number))

                elif command_id == CMD_ENQUIRE_LINK_RESP:
                    pass  # keepalive ack, nothing to do

                elif command_id == CMD_UNBIND:
                    await self._send(encode_pdu(CMD_UNBIND_RESP, STATUS_OK, sequence_number, b""))
                    raise ConnectionError("Carrier requested unbind")

                elif command_id & 0x80000000:
                    pass  # a response to something we sent; nothing to do

                else:
                    # Unknown/unhandled PDU — don't silently drop it, nack it
                    await self._send(build_generic_nack(sequence_number))
        finally:
            await self.on_status_change(self.account["id"], "disconnected")
            if self._keepalive_task:
                self._keepalive_task.cancel()
            if self._writer:
                try:
                    self._writer.close()
                except Exception:
                    pass


class SmppServer:
    """The panel acts as the SMSC (server) here — carriers connect OUTBOUND to
    us using the host/port/system_id/password they were given, and we accept
    the bind, then receive their messages as submit_sm or deliver_sm PDUs.

    One TCP listener handles every carrier: each connecting client's bind
    credentials (system_id + password) are matched against the stored SMPP
    Accounts to figure out which carrier just connected, so each company's
    OTP volume is still tracked separately."""

    def __init__(self, on_message, on_status_change, get_accounts_fn, max_connections: int = 100):
        self.on_message = on_message               # async fn(from, to, message, sms_id, company)
        self.on_status_change = on_status_change   # async fn(account_id, status)
        self.get_accounts_fn = get_accounts_fn     # sync fn() -> list of smpp account dicts
        self.max_connections = max_connections
        self._server = None
        self._sockets = 0                          # every open socket, bound or not
        self._connections: dict = {}               # account_id -> currently live writer
        self._concat = _ConcatBuffer()

    @property
    def running(self) -> bool:
        return self._server is not None

    @property
    def bound_accounts(self) -> list:
        return list(self._connections.keys())

    async def start(self, host: str, port: int):
        if self._server:
            return  # already running
        self._server = await asyncio.start_server(self._handle_client, host, port)
        addr = ", ".join(str(sock.getsockname()) for sock in self._server.sockets)
        logger.info("SMPP server listening on %s", addr)

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
            self._connections.clear()

    def _find_account(self, system_id: str, password: str):
        system_id = (system_id or "").strip()
        password = (password or "").strip()
        for acc in self.get_accounts_fn():
            if acc.get("interconnect_type") not in (None, "", "smpp", "smpp-server"):
                continue
            acc_sid = (acc.get("system_id") or "").strip()
            acc_pass = _decode_password(acc.get("password", "")).strip()
            if acc_sid == system_id and acc_pass == password:
                return acc
        return None

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peer = writer.get_extra_info("peername")
        peer_ip = peer[0] if peer else "unknown"
        write_lock = asyncio.Lock()
        account = None
        bound = False
        keepalive_task = None

        # Count every socket, not just bound ones — otherwise a flood of
        # never-binding connections slips straight past the cap.
        if self._sockets >= self.max_connections:
            logger.warning("SMPP server: rejecting %s — max connections (%s) reached",
                           peer_ip, self.max_connections)
            writer.close()
            return
        self._sockets += 1

        async def send(pdu: bytes):
            async with write_lock:
                writer.write(pdu)
                await writer.drain()

        async def keepalive_loop():
            """We send our own periodic enquire_link too (not just respond to
            theirs) — belt-and-braces against NAT/firewall connection-tracking
            silently dropping a TCP session that looks idle from the outside."""
            seq = 900000
            try:
                while not writer.is_closing():
                    await asyncio.sleep(30)
                    seq += 1
                    await send(build_enquire_link(seq))
            except Exception:
                pass

        async def ingest(msg: dict, sequence_number: int):
            if msg.get("is_delivery_receipt"):
                return
            text = msg["message"]
            if msg.get("concat"):
                key = (account["id"], msg["from"], msg["to"], msg["concat"]["ref"])
                text = self._concat.add(key, msg["concat"], text)
                if text is None:
                    return
            stamp = int(datetime.now(timezone.utc).timestamp())
            sms_id = f"smpp-{account['id']}-{sequence_number}-{stamp}"
            logger.info("SMPP server: message received from '%s' -> %s",
                        account.get("company"), msg["to"])
            await self.on_message(
                msg["from"], msg["to"], text, sms_id,
                account.get("company", account.get("system_id", "")),
            )

        try:
            logger.info("SMPP server: incoming connection from %s", peer_ip)
            while True:
                header_bytes = await asyncio.wait_for(reader.readexactly(16), timeout=120)
                command_length, command_id, command_status, sequence_number = decode_header(header_bytes)
                body = await reader.readexactly(command_length - 16) if command_length > 16 else b""

                if command_id in (CMD_BIND_TRANSCEIVER, CMD_BIND_TRANSMITTER, CMD_BIND_RECEIVER):
                    offset = 0
                    system_id, offset = _read_cstr(body, offset)
                    password, offset = _read_cstr(body, offset)
                    resp_id = {
                        CMD_BIND_TRANSCEIVER: CMD_BIND_TRANSCEIVER_RESP,
                        CMD_BIND_TRANSMITTER: CMD_BIND_TRANSMITTER_RESP,
                        CMD_BIND_RECEIVER: CMD_BIND_RECEIVER_RESP,
                    }[command_id]

                    found = self._find_account(system_id, password)
                    if not found:
                        logger.warning(
                            "SMPP server: rejected bind from %s — no account matches system_id='%s'",
                            peer_ip, system_id)
                        await send(build_bind_resp(resp_id, STATUS_INVALID_SYSID, sequence_number))
                        writer.close()
                        return

                    account = found
                    bound = True
                    self._connections[account["id"]] = writer
                    await send(build_bind_resp(resp_id, STATUS_OK, sequence_number, system_id))
                    await self.on_status_change(account["id"], "active")
                    logger.info("SMPP server: '%s' (system_id=%s) bound from %s",
                                account.get("company"), system_id, peer_ip)
                    keepalive_task = asyncio.create_task(keepalive_loop())

                elif command_id in (CMD_SUBMIT_SM, CMD_DELIVER_SM):
                    resp_builder = build_submit_sm_resp if command_id == CMD_SUBMIT_SM else build_deliver_sm_resp
                    if not bound:
                        logger.warning("SMPP server: message PDU from %s before bind — rejecting", peer_ip)
                        await send(build_generic_nack(sequence_number, STATUS_INVALID_SYSID))
                        continue
                    try:
                        msg = parse_sm_pdu(body)
                        await ingest(msg, sequence_number)
                        await send(resp_builder(sequence_number, f"MSG{sequence_number}"))
                    except Exception as exc:
                        logger.warning("SMPP server: failed to parse message PDU from %s: %s", peer_ip, exc)
                        await send(build_generic_nack(sequence_number))

                elif command_id == CMD_ENQUIRE_LINK:
                    await send(build_enquire_link_resp(sequence_number))

                elif command_id == CMD_ENQUIRE_LINK_RESP:
                    pass

                elif command_id == CMD_UNBIND:
                    await send(encode_pdu(CMD_UNBIND_RESP, STATUS_OK, sequence_number, b""))
                    logger.info("SMPP server: '%s' sent unbind",
                                account.get("company") if account else peer_ip)
                    break

                else:
                    logger.warning("SMPP server: unhandled command_id=%s from %s", hex(command_id), peer_ip)
                    await send(build_generic_nack(sequence_number))

        except asyncio.TimeoutError:
            logger.warning("SMPP server: connection from %s%s timed out (no activity for 120s)",
                           peer_ip, f" ({account.get('company','')})" if account else "")
        except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError):
            pass  # normal disconnects — nothing to log as an error
        except Exception as exc:
            logger.warning("SMPP server connection error (%s): %s", peer_ip, exc)
        finally:
            self._sockets -= 1
            if keepalive_task:
                keepalive_task.cancel()
            if account:
                # Only clear/mark-disconnected if THIS connection is still the
                # one on record — otherwise a stale disconnect could wrongly
                # wipe out a newer, already-reconnected live session.
                if self._connections.get(account["id"]) is writer:
                    self._connections.pop(account["id"], None)
                    await self.on_status_change(account["id"], "disconnected")
                    logger.info("SMPP server: '%s' disconnected (%s)", account.get("company"), peer_ip)
            try:
                writer.close()
            except Exception:
                pass


class SmppConnectionManager:
    """Tracks one SmppConnection per active outbound SMPP account. Call
    sync_with_accounts() whenever accounts are added/edited/removed so live
    connections match config."""

    def __init__(self, on_message, on_status_change):
        self.on_message = on_message
        self.on_status_change = on_status_change
        self.connections: dict = {}

    async def sync_with_accounts(self, accounts: list):
        wanted_ids = set()
        for acc in accounts:
            if acc.get("interconnect_type") != "smpp-client":
                continue  # only explicit outbound-client accounts get a managed connection
            if not acc.get("host") or not acc.get("port"):
                continue
            wanted_ids.add(acc["id"])
            if acc["id"] not in self.connections:
                conn = SmppConnection(acc, self.on_message, self.on_status_change)
                self.connections[acc["id"]] = conn
                conn.start()

        # Tear down connections whose account was deleted/disabled
        for acc_id in list(self.connections.keys()):
            if acc_id not in wanted_ids:
                await self.connections[acc_id].stop()
                del self.connections[acc_id]

    async def stop_all(self):
        for conn in list(self.connections.values()):
            await conn.stop()
        self.connections.clear()
