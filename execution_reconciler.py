import os
import subprocess
import sys
import time
from datetime import datetime

from util.execution_state import SHANGHAI, load_state, save_state

SLOTS = ("08:30", "09:30", "11:30", "13:30", "15:30", "17:30", "19:30")


def write_action_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a", encoding="utf-8") as output:
            output.write(f"{name}={value}\n")


def due_slots(now: datetime) -> list[str]:
    current_minutes = now.hour * 60 + now.minute
    return [
        slot
        for slot in SLOTS
        if int(slot[:2]) * 60 + int(slot[3:]) <= current_minutes
    ]


def run_main() -> None:
    subprocess.run([sys.executable, "main.py"], check=True)


def main() -> int:
    count_toward_daily = os.environ.get("COUNT_TOWARD_DAILY", "true").lower() == "true"
    now = datetime.now(SHANGHAI)
    today = now.date().isoformat()
    state = load_state(today)
    completed = state["completed"]

    if count_toward_daily:
        candidates = [slot for slot in due_slots(now) if slot not in completed][:1]
        if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and not candidates:
            candidates = [slot for slot in SLOTS if slot not in completed][:1]
    else:
        candidates = ["manual"]

    executed = 0
    failed = False
    for index, slot in enumerate(candidates):
        print(f"Executing slot {slot} at {now.isoformat()}", flush=True)
        try:
            run_main()
        except subprocess.CalledProcessError as error:
            print(f"Slot {slot} failed with exit code {error.returncode}", flush=True)
            failed = True
            break
        executed += 1
        if count_toward_daily:
            state = load_state(today)
            completed = state["completed"]
            completed[slot] = datetime.now(SHANGHAI).isoformat(timespec="seconds")
            save_state(state)
        if index < len(candidates) - 1:
            time.sleep(60)

    write_action_output("executed", str(executed))
    write_action_output("completed", str(len(completed)))
    print(f"Executed {executed}; completed today {len(completed)}/{len(SLOTS)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
