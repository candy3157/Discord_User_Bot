import asyncio
import contextlib
import datetime as dt

from .api_client import send_userlist
from .config import load_config
from .discord_client import DiscordClient
from .normalize import normalize_member
from .supabase_client import sync_userlist


async def run_sync_once() -> None:
    config = load_config()
    client = DiscordClient(guild_id=config.guild_id)

    await client.login(config.discord_token)
    connect_task = asyncio.create_task(client.connect())

    try:
        await client.wait_until_ready()
        raw_members = await client.fetch_all_members()
        normalized = [normalize_member(m) for m in raw_members]
        sent_at = dt.datetime.now(tz=dt.timezone.utc).isoformat()

        if config.sync_target == "supabase":
            if not config.supabase_url or not config.supabase_service_role_key:
                raise RuntimeError("Missing Supabase configuration")
            await sync_userlist(
                supabase_url=config.supabase_url,
                supabase_service_role_key=config.supabase_service_role_key,
                sent_at_iso=sent_at,
                members=normalized,
            )
        else:
            if not config.api_base_url or not config.bot_token:
                raise RuntimeError("Missing API configuration")
            await send_userlist(
                api_base_url=config.api_base_url,
                bot_token=config.bot_token,
                members=normalized,
            )
    finally:
        await client.close()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task


def run() -> None:
    asyncio.run(run_sync_once())


if __name__ == "__main__":
    run()
