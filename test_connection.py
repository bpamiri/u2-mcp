#!/usr/bin/env python3
"""Test script to verify database connection."""

from dotenv import load_dotenv

load_dotenv()  # Must run before importing config modules

from u2_mcp.config import U2Config  # noqa: E402
from u2_mcp.connection import ConnectionManager  # noqa: E402

config = U2Config()
manager = ConnectionManager(config)

print(f"Connecting to {config.host}/{config.account}...")
try:
    info = manager.connect()
    print("Connected successfully!")
    print(f"  Host: {info.host}")
    print(f"  Account: {info.account}")
    print(f"  Service: {info.service}")
    print(f"  Connected at: {info.connected_at}")

    # Test TCL command execution
    print()
    print("Testing TCL commands...")
    who = manager.execute_command("WHO")
    print(f"  WHO: {who}")

    date = manager.execute_command("DATE")
    print(f"  DATE: {date}")

    time_resp = manager.execute_command("TIME")
    print(f"  TIME: {time_resp}")

    # Test file operations
    print()
    print("Testing file operations...")
    voc = manager.open_file("VOC")
    rec = voc.read("LIST")
    print(f"  VOC LIST record: {rec}")

    # Test select list
    print()
    print("Testing select list...")
    sel = manager.create_select_list()
    sel.select(voc)
    count = 0
    ids = []
    while True:
        rec_id = sel.next()
        if rec_id is None or rec_id == "":
            break
        count += 1
        if count <= 5:
            ids.append(str(rec_id))
    print(f"  First 5 VOC IDs: {ids}")
    print(f"  Total VOC records: {count}")

    manager.disconnect()
    print()
    print("Success! All tests passed.")

except Exception as e:
    print(f"Connection failed: {type(e).__name__}: {e}")
    import traceback

    traceback.print_exc()
