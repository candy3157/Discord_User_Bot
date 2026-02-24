from dataclasses import dataclass
from typing import Optional


@dataclass
class RawMember:
    discord_id: str
    username: str
    global_name: Optional[str]
    nick: Optional[str]
    avatar_url: Optional[str]
    joined_at: Optional[str]


@dataclass
class NormalizedMember:
    discord_id: str
    display_name: str
    username: str
    avatar_url: Optional[str]
    discord_joined_at: Optional[str]


def normalize_member(raw: RawMember) -> NormalizedMember:
    display_name = raw.nick or raw.global_name or raw.username
    return NormalizedMember(
        discord_id=raw.discord_id,
        display_name=display_name,
        username=raw.username,
        avatar_url=raw.avatar_url,
        discord_joined_at=raw.joined_at,
    )
