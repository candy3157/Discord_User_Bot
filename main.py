import asyncio
import contextlib
import datetime as dt
import time

from .api_client import send_userlist
from .config import load_config
from .discord_client import DiscordClient
from .normalize import normalize_member
from .supabase_client import sync_userlist


async def run_sync_once() -> tuple[int, str, str]:
    config = load_config()
    client = DiscordClient(guild_id=config.guild_id)

    await client.login(config.discord_token)
    connect_task = asyncio.create_task(client.connect())

    try:
        await client.wait_until_ready()
        raw_members = await client.fetch_all_members()
        normalized = [normalize_member(m) for m in raw_members]
        print(
            f"[INFO] Fetched {len(normalized)} members from guild {config.guild_id}.",
            flush=True,
        )
        sent_at = dt.datetime.now(tz=dt.timezone.utc).isoformat()

        if config.sync_target == "supabase":
            if not config.supabase_url or not config.supabase_service_role_key:
                raise RuntimeError("Missing Supabase configuration")
            sync_stats = await sync_userlist(
                supabase_url=config.supabase_url,
                supabase_service_role_key=config.supabase_service_role_key,
                sent_at_iso=sent_at,
                members=normalized,
            )
            sync_summary = (
                f"added={sync_stats.added}, updated={sync_stats.updated}, "
                f"deactivated={sync_stats.deactivated}, "
                f"preserved_inactive={sync_stats.preserved_inactive}, "
                f"unchanged={sync_stats.unchanged}"
            )
        else:
            if not config.api_base_url or not config.bot_token:
                raise RuntimeError("Missing API configuration")
            await send_userlist(
                api_base_url=config.api_base_url,
                bot_token=config.bot_token,
                members=normalized,
            )
            sync_summary = f"sent={len(normalized)}"
        return len(normalized), config.sync_target, sync_summary
    finally:
        await client.close()
        connect_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await connect_task


def run() -> None:
    started = time.perf_counter()
    print("[INFO] Sync job started.", flush=True)
    try:
        synced_count, sync_target, sync_summary = asyncio.run(run_sync_once())
    except Exception as exc:
        elapsed = time.perf_counter() - started
        print(f"[ERROR] Sync job failed after {elapsed:.2f}s: {exc}", flush=True)
        raise SystemExit(1) from exc

    elapsed = time.perf_counter() - started
    print(
        f"[SUCCESS] Sync job completed in {elapsed:.2f}s "
        f"(target={sync_target}, members={synced_count}, {sync_summary}).",
        flush=True,
    )


if __name__ == "__main__":
    run()
