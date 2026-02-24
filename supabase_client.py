from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

import aiohttp

from .normalize import NormalizedMember

DEFAULT_CHUNK_SIZE = 500
DEFAULT_FETCH_PAGE_SIZE = 1000
DEFAULT_DEACTIVATE_CHUNK_SIZE = 200


@dataclass(frozen=True)
class ExistingMember:
    discord_id: str
    display_name: str
    username: str
    avatar_url: Optional[str]
    discord_joined_at: Optional[str]
    is_active: bool


@dataclass(frozen=True)
class SyncStats:
    total_incoming: int
    existing_total: int
    added: int
    updated: int
    deactivated: int
    preserved_inactive: int
    unchanged: int


def _chunked(items: list[Any], size: int) -> Iterable[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _parse_discord_id(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid discord_id: {value}") from exc


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "t", "1", "yes", "y"}
    return bool(value)


def _normalize_existing_member(row: dict[str, Any]) -> ExistingMember:
    raw_discord_id = row.get("discord_id")
    if raw_discord_id is None:
        raise ValueError("Existing member row is missing discord_id")

    avatar_url = row.get("avatar_url")
    discord_joined_at = row.get("discord_joined_at")

    return ExistingMember(
        discord_id=str(_parse_discord_id(raw_discord_id)),
        display_name=str(row.get("display_name") or ""),
        username=str(row.get("username") or ""),
        avatar_url=str(avatar_url) if avatar_url is not None else None,
        discord_joined_at=str(discord_joined_at) if discord_joined_at is not None else None,
        is_active=_coerce_bool(row.get("is_active", True)),
    )


def _member_payload(member: NormalizedMember, updated_at_iso: str, is_active: bool) -> dict[str, Any]:
    return {
        "discord_id": _parse_discord_id(member.discord_id),
        "display_name": member.display_name,
        "username": member.username,
        "avatar_url": member.avatar_url,
        "discord_joined_at": member.discord_joined_at,
        "is_active": is_active,
        "updated_at": updated_at_iso,
    }


def _is_changed(existing: ExistingMember, incoming: NormalizedMember, next_is_active: bool) -> bool:
    return (
        existing.display_name != incoming.display_name
        or existing.username != incoming.username
        or existing.avatar_url != incoming.avatar_url
        or existing.discord_joined_at != incoming.discord_joined_at
        or existing.is_active != next_is_active
    )


async def _post_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict[str, str],
    payload: list[dict[str, Any]],
) -> None:
    async with session.post(url, json=payload, headers=headers) as resp:
        if resp.status >= 400:
            text = await resp.text()
            raise RuntimeError(f"Supabase sync failed: {resp.status} {text}")


async def _patch_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> None:
    async with session.patch(url, json=payload, headers=headers) as resp:
        if resp.status >= 400:
            text = await resp.text()
            raise RuntimeError(f"Supabase patch failed: {resp.status} {text}")


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict[str, str],
) -> list[dict[str, Any]]:
    async with session.get(url, headers=headers) as resp:
        if resp.status >= 400:
            text = await resp.text()
            raise RuntimeError(f"Supabase fetch failed: {resp.status} {text}")
        data = await resp.json()
        if not isinstance(data, list):
            raise RuntimeError("Unexpected Supabase response while fetching members")
        return data


async def _fetch_existing_members(
    session: aiohttp.ClientSession,
    supabase_url: str,
    headers: dict[str, str],
    page_size: int = DEFAULT_FETCH_PAGE_SIZE,
) -> dict[str, ExistingMember]:
    select_fields = "discord_id,display_name,username,avatar_url,discord_joined_at,is_active"
    members_url = f"{supabase_url}/rest/v1/members?select={select_fields}"

    offset = 0
    existing: dict[str, ExistingMember] = {}
    while True:
        page_headers = dict(headers)
        page_headers["Range-Unit"] = "items"
        page_headers["Range"] = f"{offset}-{offset + page_size - 1}"

        rows = await _get_json(session, members_url, page_headers)
        if not rows:
            break

        for row in rows:
            normalized = _normalize_existing_member(row)
            existing[normalized.discord_id] = normalized

        if len(rows) < page_size:
            break
        offset += page_size

    return existing


async def _deactivate_missing_members(
    session: aiohttp.ClientSession,
    supabase_url: str,
    headers: dict[str, str],
    missing_ids: list[str],
    sent_at_iso: str,
    chunk_size: int = DEFAULT_DEACTIVATE_CHUNK_SIZE,
) -> int:
    if not missing_ids:
        return 0

    deactivated = 0
    for chunk in _chunked(missing_ids, chunk_size):
        csv_ids = ",".join(str(_parse_discord_id(member_id)) for member_id in chunk)
        patch_url = f"{supabase_url}/rest/v1/members?discord_id=in.({csv_ids})&is_active=eq.true"
        await _patch_json(
            session=session,
            url=patch_url,
            headers=headers,
            payload={"is_active": False, "updated_at": sent_at_iso},
        )
        deactivated += len(chunk)

    return deactivated


async def sync_userlist(
    supabase_url: str,
    supabase_service_role_key: str,
    sent_at_iso: str,
    members: List[NormalizedMember],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> SyncStats:
    headers = {
        "apikey": supabase_service_role_key,
        "Authorization": f"Bearer {supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }

    members_payload: list[dict[str, Any]] = []
    incoming_ids = {member.discord_id for member in members}

    async with aiohttp.ClientSession() as session:
        existing_map = await _fetch_existing_members(session, supabase_url, headers)

        added = 0
        updated = 0
        preserved_inactive = 0
        unchanged = 0

        for member in members:
            existing_member = existing_map.get(member.discord_id)
            if existing_member is None:
                added += 1
                members_payload.append(_member_payload(member, sent_at_iso, is_active=True))
                continue

            next_is_active = existing_member.is_active
            if not existing_member.is_active:
                preserved_inactive += 1

            if _is_changed(existing_member, member, next_is_active):
                updated += 1
                members_payload.append(_member_payload(member, sent_at_iso, is_active=next_is_active))
            else:
                unchanged += 1

        if members_payload:
            members_url = f"{supabase_url}/rest/v1/members?on_conflict=discord_id"
            for chunk in _chunked(members_payload, chunk_size):
                await _post_json(session, members_url, headers, chunk)

        missing_active_ids = [
            member_id
            for member_id, existing_member in existing_map.items()
            if member_id not in incoming_ids and existing_member.is_active
        ]
        deactivated = await _deactivate_missing_members(
            session=session,
            supabase_url=supabase_url,
            headers=headers,
            missing_ids=missing_active_ids,
            sent_at_iso=sent_at_iso,
        )

    return SyncStats(
        total_incoming=len(members),
        existing_total=len(existing_map),
        added=added,
        updated=updated,
        deactivated=deactivated,
        preserved_inactive=preserved_inactive,
        unchanged=unchanged,
    )
