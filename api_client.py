from typing import List
import aiohttp

from .normalize import NormalizedMember


async def send_userlist(
    api_base_url: str,
    bot_token: str,
    members: List[NormalizedMember],
) -> None:
    payload = {
        "members": [
            {
                "discordId": m.discord_id,
                "displayName": m.display_name,
                "username": m.username,
                "avatarUrl": m.avatar_url,
                "discordJoinedAt": m.discord_joined_at,
            }
            for m in members
        ],
    }

    headers = {"x-bot-token": bot_token, "Content-Type": "application/json"}
    url = f"{api_base_url}/api/sync/userlist"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status >= 400:
                text = await resp.text()
                raise RuntimeError(f"Sync failed: {resp.status} {text}")
