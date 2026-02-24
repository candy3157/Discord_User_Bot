import datetime as dt
from typing import List

import discord

from .normalize import RawMember


class DiscordClient(discord.Client):
    def __init__(self, guild_id: int, **kwargs):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        super().__init__(intents=intents, **kwargs)
        self.guild_id = guild_id

    async def fetch_all_members(self) -> List[RawMember]:
        await self.wait_until_ready()
        guild = self.get_guild(self.guild_id)
        if guild is None:
            guild = await self.fetch_guild(self.guild_id)

        members = []
        async for member in guild.fetch_members(limit=None):
            user = member._user
            joined_at = (
                member.joined_at.astimezone(dt.timezone.utc).isoformat()
                if member.joined_at
                else None
            )
            members.append(
                RawMember(
                    discord_id=str(member.id),
                    username=str(user),
                    global_name=user.global_name,
                    nick=member.nick,
                    avatar_url=str(user.avatar.url) if user.avatar else None,
                    joined_at=joined_at,
                )
            )

        return members
