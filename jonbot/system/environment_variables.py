import os

from dotenv import load_dotenv

load_dotenv()

# Get Bot Nick Name list
BOT_NICK_NAMES = os.getenv("BOT_NICK_NAMES").split(",")

# API Keys and tokens
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")

# Local path stuff
LOG_FILE_FOLDER_NAME = "logs"
BASE_DATA_FOLDER_NAME = f"{os.getenv('BOT_NICK_NAME')}_data"
BACKUP_FOLDER_RELATIVE_TO_HOME = os.getenv("BACKUP_FOLDER_RELATIVE_TO_HOME")

CLASSBOT_SERVER_ID = int(os.getenv("CLASSBOT_SERVER_ID"))


# Database stuff
MONGO_URI = os.getenv("MONGO_URI")
RAW_MESSAGES_COLLECTION_NAME = "raw_messages"
CHATS_COLLECTION_NAME = "chats"
USERS_COLLECTION_NAME = f"users"
CONTEXT_MEMORIES_COLLECTION_NAME = "context_memories"
ANALYSIS_COLLECTION_NAME = "analysis"

# URL stuff
URL_PREFIX = os.getenv("PREFIX")
HOST_NAME = os.getenv("HOST_NAME", "localhost")
API_HOST_NAME = "localhost"
PORT_NUMBER = int(os.getenv("PORT_NUMBER"))
if os.path.exists("/.dockerenv"):
    API_HOST_NAME = "api"
    HOST_NAME = "0.0.0.0"
    PORT_NUMBER = 8091
