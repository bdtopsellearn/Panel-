#!/usr/bin/env python3
"""GLOBAL1TEL launcher.

    python3 run.py                 # port 80 (or $PORT)
    PORT=8080 python3 run.py
"""
import os
import sys

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "80"))
    host = os.environ.get("HOST", "0.0.0.0")
    workers = int(os.environ.get("WORKERS", "1"))

    # The SMPP listener lives inside the app process, so more than one worker
    # would try to bind the same TCP port. Keep it at 1 unless SMPP is disabled.
    if workers > 1 and os.environ.get("SMPP_SERVER_ENABLED", "true").lower() in ("1", "true", "yes"):
        print("WARNING: multiple workers with the SMPP server enabled would fight over "
              "the SMPP port. Falling back to 1 worker.", file=sys.stderr)
        workers = 1

    uvicorn.run("main:app", host=host, port=port, workers=workers,
                proxy_headers=True, forwarded_allow_ips="*")
