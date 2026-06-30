import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


STATE_PATH = Path("runtime/execution_state.json")
SHANGHAI = timezone(timedelta(hours=8), name="Asia/Shanghai")


def today_shanghai() -> str:
    return datetime.now(SHANGHAI).date().isoformat()


def new_daily_state(today: str) -> dict:
    return {"date": today, "completed": {}, "last_steps": {}}


def load_state(today: str | None = None) -> dict:
    if today is None:
        today = today_shanghai()
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    if state.get("date") != today or not isinstance(state.get("completed"), dict):
        return new_daily_state(today)
    if not isinstance(state.get("last_steps"), dict):
        state["last_steps"] = {}
    return state


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = STATE_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(STATE_PATH)


def account_state_key(identifier: str, secret: bytes | str | None = None) -> str:
    message = str(identifier).encode("utf-8")
    if secret:
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        return hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hashlib.sha256(message).hexdigest()
