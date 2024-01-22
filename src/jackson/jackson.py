"""Game server management bot."""

import asyncio
from datetime import datetime, timedelta
from typing import Literal, Self
from zoneinfo import ZoneInfo

import discord
from discord import app_commands

MY_GUILD = discord.Object(id=922262091015012362)


class MyClient(discord.Client):
    """A subclass of client to sync commands."""

    def __init__(self: Self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self: Self) -> None:
        """Sync commands on ready."""
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


intents = discord.Intents.none()
client = MyClient(intents=intents)


def format_restart_message(returncode: int, stdout: str, stderr: str) -> str:
    """Format restart results as a Discord message."""
    return f"""---
    [returncode] (if this number is not `0`, something went wrong)
    `{returncode}`
    [stdout]
    ```
    {stdout}
    ```
    [stderr]
    ```
    {stderr}
    ```
    """


async def _restart_service(service: str) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_shell(
        f"sudo /bin/systemctl restart {service}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()  # type: ignore[return-value] # When would this be None?


@client.tree.command()
@app_commands.describe(game="Which game to restart")
@app_commands.checks.cooldown(1, 900, key=lambda interaction: interaction.guild_id)
async def restart_game(interaction: discord.Interaction[MyClient], game: Literal["zomboid"]) -> None:
    """Restart a game server."""
    await interaction.response.defer(thinking=True)
    returncode, stdout, stderr = await _restart_service(game)
    await interaction.followup.send(format_restart_message(returncode, stdout, stderr))


@restart_game.error
async def on_restart_game_error(
    interaction: discord.Interaction[MyClient],
    error: app_commands.AppCommandError,
) -> None:
    """Handle errors from restart_game."""
    if isinstance(error, app_commands.CommandOnCooldown):
        retry_at = datetime.now(tz=ZoneInfo("America/Chicago")) + timedelta(seconds=error.retry_after)
        await interaction.response.send_message("Try again " + discord.utils.format_dt(retry_at, style="R"))
