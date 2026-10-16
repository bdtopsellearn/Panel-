# ═══════════════════════════════════════════════════════════════════
#   GLOBAL1TEL — SMS / OTP / SMPP Reseller Panel
#   Full Setup Guide (A to Z)
# ═══════════════════════════════════════════════════════════════════

---

## Table of Contents

1. [What Is This?](#1-what-is-this)
2. [Requirements](#2-requirements)
3. [VPS Setup (Ubuntu/Debian)](#3-vps-setup-ubuntudebian)
4. [Database Setup](#4-database-setup)
5. [Panel Installation](#5-panel-installation)
6. [Configuration (.env)](#6-configuration-env)
7. [First Run](#7-first-run)
8. [Admin Panel First Login](#8-admin-panel-first-login)
9. [SMPP Setup (Carrier Connection)](#9-smpp-setup-carrier-connection)
10. [Webhook Setup (HTTP Inbound)](#10-webhook-setup-http-inbound)
11. [Creating Users (Manager → Agent → Client)](#11-creating-users-manager--agent--client)
12. [Adding Ranges & Numbers](#12-adding-ranges--numbers)
13. [How OTP Flow Works](#13-how-otp-flow-works)
14. [Running as a Service (systemd)](#14-running-as-a-service-systemd)
15. [Nginx Reverse Proxy (Domain + SSL)](#15-nginx-reverse-proxy-domain--ssl)
16. [Firewall Rules](#16-firewall-rules)
17. [Backup & Restore](#17-backup--restore)
18. [Troubleshooting](#18-troubleshooting)
19. [All Environment Variables](#19-all-environment-variables)
20. [File Structure](#20-file-structure)
21. [Bugs Fixed From Original PHP](#21-bugs-fixed-from-original-php)

---

## 1. What Is This?

GLOBAL1TEL is a **complete SMS/OTP reseller panel** with:

- **Admin Panel** — full control: managers, agents, clients, ranges, numbers,
  SMPP accounts, live sessions, CDR reports, statistics, payment requests
- **Manager Panel** — manage agents, allocate numbers, view stats & CDR
- **Agent Panel** — manage clients, allocate numbers, view stats & CDR
- **Client Panel** — view assigned numbers, incoming OTPs, test SMS
- **SMPP Server** — carriers connect and deliver SMS/OTP directly
- **HTTP Webhook** — receive SMS via HTTP POST from any provider
- **Automatic billing** — per-OTP payout to client → agent → manager
- **Never-lose-an-OTP** — disk spool + auto-replay when DB is temporarily down

**Stack:** Python 3.10+ / FastAPI / PyMySQL / MariaDB (or MySQL)

---

## 2. Requirements

| Item | Minimum |
|---|---|
| OS | Ubuntu 20.04+ / Debian 11+ (any Linux works) |
| Python | 3.10 or higher |
| Database | MariaDB 10.5+ or MySQL 8.0+ |
| RAM | 512 MB (1 GB recommended) |
| Disk | 500 MB free |
| Ports | 80 (HTTP), 2775 (SMPP), 3306 (MySQL) |

---

## 3. VPS Setup (Ubuntu/Debian)

**Step 1 — Update system:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Step 2 — Install Python 3 + pip:**
```bash
sudo apt install -y python3 python3-pip python3-venv
python3 --version    # must show 3.10+
```

**Step 3 — Install MariaDB:**
```bash
sudo apt install -y mariadb-server mariadb-client
sudo systemctl enable mariadb
sudo systemctl start mariadb
sudo mysql_secure_installation
```
During `mysql_secure_installation`:
- Set root password → YES (remember this password)
- Remove anonymous users → YES
- Disallow root login remotely → YES
- Remove test database → YES
- Reload privilege tables → YES

**Step 4 — Verify database is running:**
```bash
sudo mariadb -uroot -p -e "SELECT VERSION();"
```

---

## 4. Database Setup

**Step 1 — Upload GLOBAL1TEL folder to your VPS:**
```bash
# From your local machine:
scp -r GLOBAL1TEL/ root@YOUR_VPS_IP:/opt/

# Or use FileZilla/WinSCP to upload to /opt/GLOBAL1TEL/
```

**Step 2 — Create database and user:**
```bash
cd /opt/GLOBAL1TEL
sudo mariadb -uroot -p < database/00-create-db-user.sql
```

This creates:
- Database: `global1tel`
- User: `global1tel_user` with password `global1tel_secure_pass_2026`
- Full privileges on the database

**Step 3 — Import schema (all tables):**
```bash
sudo mariadb -uroot -p global1tel < database/schema.sql
```

**Step 4 — Run SMPP migration (required for carrier connections):**
```bash
sudo mariadb -uroot -p global1tel < database/migrations/smpp_bind_credentials_upgrade.sql
```

**Step 5 — Verify tables exist:**
```bash
sudo mariadb -uroot -p global1tel -e "SHOW TABLES;"
```
You should see 15+ tables including `users`, `sms_numbers`, `sms_ranges`,
`sms_cdr`, `smpp_cdr`, `smpp_users`, `smpp_config`, etc.

---

## 5. Panel Installation

**Step 1 — Install Python dependencies:**
```bash
cd /opt/GLOBAL1TEL
pip3 install -r requirements.txt
```

The dependencies are:
- `fastapi` — web framework
- `uvicorn` — ASGI server
- `pymysql` — MySQL connector (pure Python, no compiler needed)
- `itsdangerous` — signed cookie sessions
- `python-multipart` — file upload / form parsing

**Step 2 — Verify installation:**
```bash
python3 -c "import fastapi, uvicorn, pymysql, itsdangerous; print('ALL OK')"
```

---

## 6. Configuration (.env)

**Edit the config file:**
```bash
nano /opt/GLOBAL1TEL/config/.env
```

**Change these values:**

```env
# ─── DATABASE ────────────────────────────────────────────
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=global1tel
DB_USER=global1tel_user
DB_PASS=global1tel_secure_pass_2026    # ← change if you used a different password

# ─── APPLICATION ─────────────────────────────────────────
APP_NAME=GLOBAL1TEL
APP_URL=http://YOUR_DOMAIN_OR_IP:80    # ← your actual URL
APP_ENV=production
APP_DEBUG=false                        # ← keep false in production

# ─── SECURITY (IMPORTANT — CHANGE THESE!) ────────────────
SALT=mbc_sms_secure_salt_2024          # ← DO NOT change after users are created
                                       #    (changing it breaks all passwords)

SMPP_WEBHOOK_KEY=PUT_A_LONG_RANDOM_STRING_HERE
#   ↑ This key authenticates incoming webhook requests.
#     Generate one: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

G1T_SECRET=PUT_ANOTHER_LONG_RANDOM_STRING_HERE
#   ↑ Signs session cookies. If blank, a default is used (less secure).
#     Generate one: python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# ─── SMPP SERVER ─────────────────────────────────────────
SMPP_SERVER_ENABLED=true               # ← true = carriers can connect
SMPP_SERVER_HOST=0.0.0.0               # ← listen on all interfaces
SMPP_SERVER_PORT=2775                  # ← standard SMPP port
```

**IMPORTANT WARNINGS:**
- `SALT` → NEVER change after the first user is created. Changing it makes
  every existing password invalid.
- `SMPP_WEBHOOK_KEY` → Set a strong random value. Without it, anyone can
  send fake OTPs to your panel.
- `G1T_SECRET` → Set a strong random value. It protects login sessions.

---

## 7. First Run

**Quick test (foreground):**
```bash
cd /opt/GLOBAL1TEL
PORT=8080 python3 run.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8080
INFO:     SMPP server listening on 0.0.0.0:2775
```

**Open in browser:**
```
http://YOUR_VPS_IP:8080
```

You should see the GLOBAL1TEL login page with the gold G1 logo.

**Stop with:** `Ctrl + C`

---

## 8. Admin Panel First Login

**Default admin credentials:**
```
Username: admin
Password: G1TAdmin@2026!
```

**Steps:**
1. Go to `http://YOUR_VPS_IP:8080/ints/login`
2. Enter username: `admin`
3. Enter password: `G1TAdmin@2026!`
4. Solve the captcha (simple math)
5. Click LOGIN

**FIRST THING TO DO:** Change the admin password!
- Go to Profile (bottom of sidebar)
- Enter new password
- Save

**Admin can also login at:**
```
http://YOUR_VPS_IP:8080/adminlogin
```

---

## 9. SMPP Setup (Carrier Connection)

This is how carriers deliver SMS/OTP to your panel.

**Step 1 — Create SMPP Account (in Admin Panel):**
1. Login as admin
2. Go to **SMPP Accounts** (sidebar)
3. Click **Add Account**
4. Fill in:
   - **Username/System ID:** e.g. `MyCarrier` (give this to the carrier)
   - **Password:** e.g. `SecurePass123` (give this to the carrier)
   - **Supplier Name:** e.g. `My Carrier Inc`
   - **Bind Type:** `TR` (transceiver — most common)
   - **Status:** `Active`
5. Save

**Step 2 — Give carrier your connection details:**
```
Host: YOUR_VPS_IP
Port: 2775
System ID: MyCarrier          (what you set above)
Password: SecurePass123       (what you set above)
Bind Type: Transceiver
SMPP Version: 3.4
```

**Step 3 — Verify connection:**
- Go to **SMPP Sessions** in admin sidebar
- When the carrier connects, you will see their session with status "Active"
- `total_messages` counter will increase with each SMS received

**Supported SMS encodings (all automatic):**
- ASCII (data_coding=0)
- GSM 03.38 (data_coding=0, with GSM charset)
- Latin-1 (data_coding=3)
- UCS-2 / UTF-16 (data_coding=8) — for Arabic, Chinese, etc.
- TLV message_payload (sm_length=0)
- Concatenated / multi-part SMS (UDH, esm_class=0x40)

---

## 10. Webhook Setup (HTTP Inbound)

Alternative to SMPP — receive SMS via HTTP POST.

**Endpoint:**
```
POST http://YOUR_VPS_IP:8080/api/smpp.php?action=receive
```

**Headers:**
```
Content-Type: application/json
X-API-KEY: YOUR_SMPP_WEBHOOK_KEY     (from config/.env)
```

**Body (JSON):**
```json
{
  "source_addr": "Google",
  "destination_addr": "959692514720",
  "short_message": "Your verification code is 483920",
  "message_id": "unique-id-123"
}
```

**Response (success):**
```json
{"success": true, "assigned": true, "cdr_id": 42}
```

**Response (unknown number):**
```json
{"success": true, "assigned": false, "message": "Number not assigned"}
```

Give this URL and your `SMPP_WEBHOOK_KEY` to your SMS provider.

---

## 11. Creating Users (Manager → Agent → Client)

The hierarchy is: **Admin → Manager → Agent → Client**

**Create Manager (Admin does this):**
1. Login as Admin
2. Go to **Managers** → **Add Manager**
3. Fill username, password, email, full name
4. Save
5. Add balance: **Credit Notes** → select manager → add amount

**Create Agent (Manager does this):**
1. Login as Manager
2. Go to **My Agents** → **Add Agent**
3. Fill username, password, email
4. Save

**Create Client (Agent does this):**
1. Login as Agent
2. Go to **My Clients** → **Add Client**
3. Fill username, password, email
4. Save

**Or Admin can create all roles** from the admin panel.

---

## 12. Adding Ranges & Numbers

**Create a Range (Admin):**
1. Go to **SMS Ranges** → **Add Range**
2. Fill in:
   - **Range Name:** e.g. `Myanmar_Mytel`
   - **Prefix:** e.g. `9596` (number prefix for matching)
   - **Currency:** e.g. `USD`
   - **Payout rates:** how much to pay per OTP
     - 1/1 = pay every OTP
     - 7/1 = pay on 1st OTP per 7-day window
     - etc.
3. Save

**Add Numbers to a Range (Admin/Manager):**
1. Go to **All Numbers** → **Add Numbers**
2. Enter numbers (one per line): `959692514720`
3. Select range
4. Save

**Assign Numbers to Clients (Agent):**
1. Go to **My SMS Numbers**
2. Select unassigned numbers
3. Assign to client
4. Set pay term (1/1, 7/1, etc.)

---

## 13. How OTP Flow Works

```
Carrier ──SMPP bind──→ GLOBAL1TEL (port 2775)
         ──deliver_sm──→ Engine decodes message
                          ↓
                    ┌─────────────────────────┐
                    │  ingest_sms() pipeline   │
                    ├─────────────────────────┤
                    │ 1. Save raw to smpp_cdr  │
                    │ 2. Find matching number  │
                    │ 3. Detect OTP in text    │
                    │ 4. Calculate payouts     │
                    │ 5. Credit balances       │
                    │    Client: full rate      │
                    │    Agent:  10% of rate    │
                    │    Manager: 5% of rate    │
                    │ 6. Save to sms_cdr       │
                    │ 7. Send notifications     │
                    └─────────────────────────┘
                          ↓
              Client sees OTP in their dashboard
```

**If database is down when OTP arrives:**
```
deliver_sm → ingest fails → message saved to var/spool/inbound.jsonl
                              ↓
              background task retries every 60 seconds
                              ↓
              database comes back → message stored → spool cleared
```
**No OTP is ever lost.**

---

## 14. Running as a Service (systemd)

**Create service file:**
```bash
sudo nano /etc/systemd/system/global1tel.service
```

**Paste this:**
```ini
[Unit]
Description=GLOBAL1TEL SMS/OTP Panel
After=network.target mariadb.service
Requires=mariadb.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/GLOBAL1TEL
Environment="PORT=8080"
Environment="SMPP_SERVER_ENABLED=true"
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable global1tel
sudo systemctl start global1tel
sudo systemctl status global1tel
```

**Useful commands:**
```bash
sudo systemctl restart global1tel    # restart
sudo systemctl stop global1tel       # stop
sudo journalctl -u global1tel -f     # view live logs
```

---

## 15. Nginx Reverse Proxy (Domain + SSL)

**Step 1 — Install Nginx + Certbot:**
```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

**Step 2 — Create Nginx config:**
```bash
sudo nano /etc/nginx/sites-available/global1tel
```

**Paste this:**
```nginx
server {
    listen 80;
    server_name your-domain.com;      # ← change to your domain

    client_max_body_size 5M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (for live updates if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Step 3 — Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/global1tel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Step 4 — Get SSL certificate (free):**
```bash
sudo certbot --nginx -d your-domain.com
```

**Step 5 — Update .env:**
```env
APP_URL=https://your-domain.com
```

Now your panel runs on `https://your-domain.com` with SSL.

---

## 16. Firewall Rules

```bash
# Allow SSH
sudo ufw allow 22

# Allow HTTP + HTTPS (for web panel)
sudo ufw allow 80
sudo ufw allow 443

# Allow SMPP (for carrier connections)
sudo ufw allow 2775

# Enable firewall
sudo ufw enable
sudo ufw status
```

**Do NOT expose port 3306 (MySQL) to the internet.**

---

## 17. Backup & Restore

**Backup database:**
```bash
# Daily backup (add to crontab)
mysqldump -uglobal1tel_user -p'global1tel_secure_pass_2026' global1tel > /opt/backups/global1tel_$(date +%Y%m%d).sql
```

**Restore from backup:**
```bash
mariadb -uroot -p global1tel < /opt/backups/global1tel_20260831.sql
```

**Backup whole panel:**
```bash
tar -czf /opt/backups/global1tel_full_$(date +%Y%m%d).tar.gz /opt/GLOBAL1TEL/
```

**Auto-backup cron (every day at 3am):**
```bash
crontab -e
# Add this line:
0 3 * * * mysqldump -uglobal1tel_user -p'global1tel_secure_pass_2026' global1tel | gzip > /opt/backups/global1tel_$(date +\%Y\%m\%d).sql.gz
```

---

## 18. Troubleshooting

**Panel won't start:**
```bash
# Check if port is already in use
ss -tlnp | grep 8080
ss -tlnp | grep 2775

# Kill stuck processes
pkill -f "python3 run.py"

# Check logs
journalctl -u global1tel --no-pager -n 50
```

**Can't login:**
```bash
# Reset admin password directly in database
SALT="mbc_sms_secure_salt_2024"
NEW_PASS="NewPassword123!"
HASH=$(python3 -c "import hashlib; print(hashlib.sha256(('${SALT}${NEW_PASS}').encode()).hexdigest())")
mariadb -uroot -p global1tel -e "UPDATE users SET password='${HASH}' WHERE username='admin';"
```

**SMPP carrier can't connect:**
```bash
# Check SMPP port is open
ss -tlnp | grep 2775

# Check firewall
sudo ufw status | grep 2775

# Check SMPP account exists and is active
mariadb -uroot -p global1tel -e "SELECT username, system_id, status, bind_password FROM smpp_users;"
# bind_password must NOT be empty — if it is, re-save the account in admin panel
```

**OTPs not showing for client:**
```bash
# Check if number is assigned
mariadb -uroot -p global1tel -e "SELECT number, status, assigned_to FROM sms_numbers WHERE number='959692514720';"
# status must be 'assigned' and assigned_to must be a user_id

# Check raw incoming messages
mariadb -uroot -p global1tel -e "SELECT * FROM smpp_cdr ORDER BY id DESC LIMIT 10;"

# Check processed messages
mariadb -uroot -p global1tel -e "SELECT * FROM sms_cdr ORDER BY id DESC LIMIT 10;"

# Check spool (messages waiting for DB)
cat /opt/GLOBAL1TEL/var/spool/inbound.jsonl 2>/dev/null || echo "Spool empty (good)"
```

**Database upgrade needed:**
```bash
# Option 1: One-click in admin panel
# Login as admin → Settings → Database Upgrade

# Option 2: Manual
mariadb -uroot -p global1tel < database/migrations/smpp_bind_credentials_upgrade.sql
```

---

## 19. All Environment Variables

| Variable | Default | What It Does |
|---|---|---|
| `PORT` | `80` | HTTP listen port |
| `HOST` | `0.0.0.0` | HTTP listen address |
| `WORKERS` | `1` | Uvicorn workers (keep 1 with SMPP) |
| `DB_HOST` | `127.0.0.1` | MySQL/MariaDB host |
| `DB_PORT` | `3306` | MySQL/MariaDB port |
| `DB_NAME` | `global1tel` | Database name |
| `DB_USER` | `global1tel_user` | Database username |
| `DB_PASS` | `global1tel_secure_pass_2026` | Database password |
| `APP_NAME` | `GLOBAL1TEL` | Panel display name |
| `APP_URL` | `http://127.0.0.1:8080` | Public URL |
| `APP_ENV` | `production` | Environment mode |
| `APP_DEBUG` | `false` | Debug mode (keep false) |
| `SALT` | `mbc_sms_secure_salt_2024` | Password hash salt — NEVER CHANGE |
| `G1T_SECRET` | (auto-generated) | Session cookie signing key |
| `SESSION_LIFETIME` | `7200` | Session timeout in seconds (2 hours) |
| `SESSION_NAME` | `global1tel_session` | Cookie name |
| `SMPP_SERVER_ENABLED` | `true` | Start SMPP listener on boot |
| `SMPP_SERVER_HOST` | `0.0.0.0` | SMPP listen address |
| `SMPP_SERVER_PORT` | `2775` | SMPP listen port |
| `SMPP_WEBHOOK_KEY` | (blank) | Webhook auth key — SET THIS |
| `SMS_SPOOL_DIR` | `var/spool` | Disk spool directory for failed ingests |

---

## 20. File Structure

```
GLOBAL1TEL/
├── main.py                  ← FastAPI app (routes, middleware, spool task)
├── run.py                   ← Start script (python3 run.py)
├── requirements.txt         ← Python dependencies
├── README.md                ← This file
│
├── config/
│   └── .env                 ← All configuration (database, SMPP, secrets)
│
├── core/
│   ├── config.py            ← Loads .env settings
│   ├── db.py                ← MySQL connection pool
│   ├── helpers.py           ← Password hashing, notifications, balance ops
│   ├── session.py           ← Signed cookies + rate limiter
│   ├── context.py           ← Request context (auth checks)
│   ├── smpp_client.py       ← SMPP v3.4 protocol engine (all encodings)
│   ├── smpp_service.py      ← SMPP lifecycle (start/stop, account loading)
│   ├── sms_ingest.py        ← Single OTP processing pipeline
│   └── sms_spool.py         ← Disk safety net (never lose an OTP)
│
├── api/
│   ├── auth.py              ← Login / logout
│   ├── dashboard.py         ← Dashboard stats (per role)
│   ├── admin.py             ← All admin actions (users, SMPP, settings)
│   ├── users.py             ← User management
│   ├── numbers.py           ← Number management
│   ├── ranges.py            ← Range management
│   ├── cdr.py               ← CDR reports
│   ├── smpp.py              ← SMPP control + webhook receiver
│   ├── test_sms.py          ← SMS test panel
│   ├── misc.py              ← Profile, notifications, news
│   └── legacy.py            ← DataTables/select2 endpoints
│
├── database/
│   ├── 00-create-db-user.sql        ← Run first (creates DB + user)
│   ├── schema.sql                   ← Full table schema
│   └── migrations/
│       └── smpp_bind_credentials_upgrade.sql   ← SMPP bind columns
│
├── public/
│   └── ints/                ← All HTML pages + CSS + JS + images
│       ├── login.html
│       ├── admin/
│       ├── manager/
│       ├── agent/
│       ├── client/
│       └── assets/
│           ├── css/
│           ├── js/
│           └── img/
│               ├── brand/global1tel-logo.png
│               ├── global1tel-icon.svg
│               └── global1tel-mark.svg
│
└── var/
    └── spool/               ← Auto-created, stores failed OTPs temporarily
        ├── inbound.jsonl    ← Messages waiting for DB replay
        └── inbound.failed.jsonl   ← Messages that failed 50+ times
```

---

## 21. Bugs Fixed From Original PHP

| # | Bug | Impact |
|---|---|---|
| 1 | HTTP Provider save → 500 | Settings page crashed |
| 2 | Fake "Jasmin running" status | Always showed running even when dead |
| 3 | Inbound webhook disabled by default | No SMS could arrive via HTTP |
| 4 | HTTP Provider was a dead form | Saved data, connected to nothing |
| 5 | No SMPP server existed | Depended on external Jasmin, never shipped |
| 6 | Dashboard chart 500 for managers | Undefined variable in SQL |
| 7 | SMPP bind never worked | One-way hash vs plaintext bind PDU = every OTP lost |
| 8 | Column mismatch | Service read wrong column names |
| 9 | Status ENUM overwrite | Engine un-suspended admin-disabled accounts |
| 10 | OTP detection missed "code"/"pin" | Most common OTP wording never flagged |
| 11 | Duplicate webhook → 500 | KeyError on deduplicate path |
| 12 | total_messages always 0 | Per-carrier counter never written |

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│              GLOBAL1TEL Quick Reference            │
├──────────────────────────────────────────────────┤
│                                                    │
│  Start:    PORT=8080 python3 run.py               │
│  Stop:     Ctrl+C  (or systemctl stop global1tel) │
│  Logs:     journalctl -u global1tel -f            │
│                                                    │
│  Web:      http://YOUR_IP:8080                    │
│  SMPP:     YOUR_IP:2775                           │
│                                                    │
│  Admin:    admin / G1TAdmin@2026!                 │
│                                                    │
│  Config:   config/.env                            │
│  Spool:    var/spool/inbound.jsonl                │
│                                                    │
│  DB Reset: mariadb -uroot -p global1tel           │
│            < database/schema.sql                  │
│                                                    │
│  Webhook:  POST /api/smpp.php?action=receive      │
│            Header: X-API-KEY: <webhook_key>       │
│                                                    │
│  ⚠ NEVER change SALT after users are created      │
│  ⚠ ALWAYS set SMPP_WEBHOOK_KEY before going live  │
│  ⚠ ALWAYS set G1T_SECRET before going live        │
│                                                    │
└──────────────────────────────────────────────────┘
```

---

