import os
from pathlib import Path


def _load_keys_from_env() -> list[str]:
    """Load Gemini API keys from environment variable or .env file."""
    env_val = os.environ.get("GEMINI_API_KEYS", "")
    if not env_val:
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEYS="):
                    env_val = line.split("=", 1)[1].strip()
                    break
    keys = [k.strip() for k in env_val.split(",") if k.strip()]
    return list(dict.fromkeys(keys))


api_list = _load_keys_from_env()
n_apis = len(api_list)
api_request_threshold = 1
api_idx = 0
