import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

_DEFAULT_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_DEFAULT_ENV_PATH)


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value


@dataclass(frozen=True)
class BotConfig:
    discord_token: str
    guild_id: int
    sync_target: str
    api_base_url: Optional[str]
    bot_token: Optional[str]
    supabase_url: Optional[str]
    supabase_service_role_key: Optional[str]


def load_config() -> BotConfig:
    sync_target = os.getenv("SYNC_TARGET", "supabase").strip().lower()
    if sync_target not in ("supabase", "api"):
        raise RuntimeError("SYNC_TARGET must be 'supabase' or 'api'")

    return BotConfig(
        discord_token=_require("DISCORD_TOKEN"),
        guild_id=int(_require("DISCORD_GUILD_ID")),
        sync_target=sync_target,
        api_base_url=_require("API_BASE_URL").rstrip("/") if sync_target == "api" else None,
        bot_token=_require("BOT_TOKEN") if sync_target == "api" else None,
        supabase_url=_require("SUPABASE_URL").rstrip("/") if sync_target == "supabase" else None,
        supabase_service_role_key=(
            _require("SUPABASE_SERVICE_ROLE_KEY") if sync_target == "supabase" else None
        ),
    )
