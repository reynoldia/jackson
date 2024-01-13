"""Game server management bot."""

from os import getenv

from .jackson import client

if __name__ == "__main__":
    token = getenv("BOT_TOKEN")
    if token is None:
        msg = "BOT_TOKEN not set"
        raise RuntimeError(msg)
    client.run(token)
