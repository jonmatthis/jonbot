import os

from dotenv import load_dotenv

load_dotenv()
BASE_DATA_FOLDER_NAME = f"{os.getenv('BOT_NAME')}_data"

DATABASE_BACKUP = "database_backup"

LOG_FILE_FOLDER_NAME = "logs"
DISCORD_BOT_TOKEN = os.getenv("DISCORD_TOKEN")

DIRECT_MESSAGES_ALLOWED = True if os.getenv("DIRECT_MESSAGES_ALLOWED") == "True" else False

OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")



TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_NAME = os.getenv('BOT_NAME')
MONGO_URI = os.getenv('MONGO_URI')
URL_PREFIX = os.getenv('PREFIX')
HOST_NAME = os.getenv('HOST_NAME', 'localhost')
PORT_NUMBER = int(os.getenv('PORT_NUMBER', 5000))

def get_allowed_channels():
    ALLOWED_CHANNELS = os.getenv("ALLOWED_CHANNELS")
    if ALLOWED_CHANNELS is None:
        raise ValueError("ALLOWED_CHANNELS environment variable not set.")

    if ALLOWED_CHANNELS == "ALL":
        return ALLOWED_CHANNELS
    else:
        return [int(channel_id) for channel_id in ALLOWED_CHANNELS.split(",")]

ALLOWED_CHANNELS = get_allowed_channels()