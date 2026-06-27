import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


SLOTS = ("08:30", "09:30", "11:30", "13:30", "15:30", "17:30", "19:30")
STATE_PATH = Path("runtime/execution_state.json")
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")


def load_state(today: str) -> dict:
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    if state.get("date") != today or not isinstance(state.get("completed"), dict):
        return {"date": today, "completed": {}}
    return state


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(STATE_PATH)


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
    state = load_state(now.date().isoformat())
    completed = state["completed"]

    if count_toward_daily:
        candidates = [slot for slot in due_slots(now) if slot not in completed]
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
