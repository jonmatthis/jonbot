import os
from pathlib import Path

import toml
from dotenv import load_dotenv

load_dotenv()


try:
    BOT_NICK_NAME = os.environ["BOT_NICK_NAME"]
except KeyError:
    raise EnvironmentError("BOT_NICK_NAME environment variable not found!")

# Load the configuration from the TOML file.
path_to_discord_config_folder = "bot_tomls"
config_path = Path(__file__).parent / path_to_discord_config_folder/ f"{BOT_NICK_NAME}_config.toml"
config = toml.load(config_path.resolve())

# Extract the desired values.
assert config.get("bot_nick_name") == BOT_NICK_NAME, f"Bot nick name doesn't match what's in {str(config_path)}"
DISCORD_TOKEN = config.get("discord_token")
if DISCORD_TOKEN is None:
    raise ValueError("discord_token not found in the TOML config!")

ALLOWED_SERVERS = config.get("allowed_servers")
if not ALLOWED_SERVERS:
    raise ValueError("allowed_servers not found or is empty in the TOML config!")

DIRECT_MESSAGES_ALLOWED = config.get("direct_messages_allowed")
if DIRECT_MESSAGES_ALLOWED is None:
    raise ValueError("direct_messages_allowed not found in the TOML config!")

# Assuming you want to create dictionaries for each server's details
# For example: SERVERS_DETAILS["M Y 🌱"] will give you a dictionary of that server's environment_config.
SERVERS_DETAILS = {}
for server_name in ALLOWED_SERVERS:
    SERVERS_DETAILS[server_name] = config.get(server_name, {})
