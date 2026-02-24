from typing import Iterable, List
import aiohttp

from .normalize import NormalizedMember

DEFAULT_CHUNK_SIZE = 500


def _chunked(items: List[dict], size: int) -> Iterable[List[dict]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _parse_discord_id(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid discord_id: {value}") from exc


def _member_payload(member: NormalizedMember, updated_at_iso: str) -> dict:
    return {
        "discord_id": _parse_discord_id(member.discord_id),
        "display_name": member.display_name,
        "username": member.username,
        "avatar_url": member.avatar_url,
        "discord_joined_at": member.discord_joined_at,
        "is_active": True,
        "updated_at": updated_at_iso,
    }


async def _post_json(session: aiohttp.ClientSession, url: str, headers: dict, payload: list) -> None:
    async with session.post(url, json=payload, headers=headers) as resp:
        if resp.status >= 400:
            text = await resp.text()
            raise RuntimeError(f"Supabase sync failed: {resp.status} {text}")


async def sync_userlist(
    supabase_url: str,
    supabase_service_role_key: str,
    sent_at_iso: str,
    members: List[NormalizedMember],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> None:
    headers = {
        "apikey": supabase_service_role_key,
        "Authorization": f"Bearer {supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    members_payload = [_member_payload(m, sent_at_iso) for m in members]

    async with aiohttp.ClientSession() as session:
        if members_payload:
            members_url = f"{supabase_url}/rest/v1/members?on_conflict=discord_id"
            for chunk in _chunked(members_payload, chunk_size):
                await _post_json(session, members_url, headers, chunk)

        # bot_status sync removed by request
