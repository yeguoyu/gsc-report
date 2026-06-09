"""Create runtime secret files from GitHub Actions secrets."""

import base64
import json
import os
import sys
from pathlib import Path


SECRET_FILES = [
    ("GSC_CLIENT_SECRET_JSON", "GSC_CLIENT_SECRET_JSON_B64", "client_secret.json", True),
    ("GSC_TOKEN_JSON", "GSC_TOKEN_JSON_B64", "token.json", True),
    ("GA4_TOKEN_JSON", "GA4_TOKEN_JSON_B64", "token_ga4.json", False),
]

REQUIRED_ENV = [
    "FEISHU_WEBHOOK",
    "FEISHU_APP_ID",
    "FEISHU_APP_SECRET",
    "BITABLE_APP_TOKEN",
]

REQUIRED_ANY_ENV = [
    ("FEISHU_CHAT_ID", "FEISHU_FILE_CHAT_ID"),
]


def _read_secret(raw_name, b64_name, required):
    raw_value = os.getenv(raw_name)
    b64_value = os.getenv(b64_name)

    if raw_value:
        return raw_value

    if b64_value:
        try:
            return base64.b64decode(b64_value).decode("utf-8")
        except Exception as exc:
            raise ValueError(f"{b64_name} is not valid base64: {exc}") from exc

    if required:
        raise ValueError(f"Missing required secret {raw_name} or {b64_name}")

    return None


def _write_json_secret(raw_name, b64_name, path, required):
    value = _read_secret(raw_name, b64_name, required)
    if value is None:
        return

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{raw_name}/{b64_name} is not valid JSON: {exc}") from exc

    Path(path).write_text(json.dumps(parsed, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] wrote {path}")


def main():
    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    missing.extend(
        " or ".join(names)
        for names in REQUIRED_ANY_ENV
        if not any(os.getenv(name) for name in names)
    )
    if missing:
        print("[ERROR] Missing required environment variables: " + ", ".join(missing))
        return 1

    for raw_name, b64_name, path, required in SECRET_FILES:
        try:
            _write_json_secret(raw_name, b64_name, path, required)
        except ValueError as exc:
            print(f"[ERROR] {exc}")
            return 1

    Path("reports").mkdir(exist_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
