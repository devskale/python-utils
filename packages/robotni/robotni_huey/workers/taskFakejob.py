import time
import random
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "fakejob.log")
MAX_ENTRIES = 100

def _read_log_entries():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return f.readlines()

def _write_log_entries(entries):
    with open(LOG_FILE, "w") as f:
        f.writelines(entries)

def _get_next_id(entries):
    if not entries:
        return 0
    # Extract id from the first line (since newest is on top)
    first_line = entries[0]
    if first_line.startswith("#"):
        try:
            return int(first_line.split(":", 1)[0][1:]) + 1
        except Exception:
            pass
    # Fallback: scan all lines for max id
    max_id = -1
    for line in entries:
        if line.startswith("#"):
            try:
                id_val = int(line.split(":", 1)[0][1:])
                if id_val > max_id:
                    max_id = id_val
            except Exception:
                continue
    return max_id + 1

def taskFakejob():
    duration = random.randint(3, 15)
    start = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    time.sleep(duration)
    end = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    entries = _read_log_entries()
    next_id = _get_next_id(entries)
    msg = f"#{next_id}: i fakeWorked from {start} to {end} for {duration} seconds\n"
    print("Fake job completed")
    # Insert newest at the top
    entries = [msg] + entries
    if len(entries) > MAX_ENTRIES:
        entries = entries[:MAX_ENTRIES]
    _write_log_entries(entries)
    return msg
