from datetime import datetime
from pathlib import Path
from typing import Union, Optional

from jonbot.system.environment_variables import (
    BASE_DATA_FOLDER_NAME,
    LOG_FILE_FOLDER_NAME,
    BACKUP_FOLDER_RELATIVE_TO_HOME,
)


def os_independent_home_dir():
    return str(Path.home())


def get_backups_folder_path():
    backups_folder_path = Path().home() / BACKUP_FOLDER_RELATIVE_TO_HOME
    backups_folder_path.mkdir(exist_ok=True, parents=True)
    return str(backups_folder_path)


def get_log_file_path():
    log_folder_path = Path(get_base_data_folder_path()) / LOG_FILE_FOLDER_NAME
    log_folder_path.mkdir(exist_ok=True, parents=True)
    log_file_path = log_folder_path / create_log_file_name()
    return str(log_file_path)


def get_base_data_folder_path(
        parent_folder: Union[str, Path] = os_independent_home_dir()
):
    base_folder_path = Path(parent_folder) / BASE_DATA_FOLDER_NAME

    if not base_folder_path.exists():
        base_folder_path.mkdir(exist_ok=True, parents=True)

    return str(base_folder_path)


SAMPLE_DISCORD_MESSAGE_FILE_NAME = "sample_discord_message.json"
get_sample_discord_message_json_path = lambda: str(
    Path(get_base_data_folder_path()) / SAMPLE_DISCORD_MESSAGE_FILE_NAME
)


def get_new_attachments_folder_path():
    return str(
        Path(get_base_data_folder_path())
        / "attachments"
        / f"{get_current_date_time_string()}"
    )


def create_log_file_name():
    return "log_" + get_current_date_time_string() + ".log"


def get_current_date_time_string():
    return datetime.now().isoformat().replace(":", "_").replace(".", "_")


def clean_path_string(filename: str):
    return filename.replace(":", "_").replace(".", "_").replace(" ", "_")


def get_default_backup_save_path(filename: str,
                                 subfolder: str = None,
                                 precise_timestamp: bool = False,
                                 filetype: Optional[str] = "json") -> str:
    backup_path = Path(get_backups_folder_path())
    if subfolder:
        backup_path = backup_path / subfolder
    backup_path.mkdir(exist_ok=True, parents=True)

    if filetype is not None:
        if not filetype.startswith("."):
            filetype = "." + filetype

        if filename.endswith(filetype):
            filename.replace(filetype, "")
    else:
        filetype = ""
    filename = clean_path_string(filename)

    if precise_timestamp:
        filename += f"_{get_current_date_time_string()}"  # full timestamp, down to the millisecond lol
    else:
        filename += f"_{get_current_date_time_string()[:10]}"  # just the date

    filename += filetype
    save_path = backup_path / filename
    return str(save_path)


def get_chroma_vector_store_path() -> str:
    vector_stor_path = Path(get_base_data_folder_path()) / "chroma_vectorstore_persistence"
    vector_stor_path.mkdir(exist_ok=True, parents=True)
    return str(vector_stor_path)


def get_temp_folder() -> str:
    temp_folder = Path(get_base_data_folder_path()) / "tmp"
    temp_folder.mkdir(exist_ok=True, parents=True)
    return str(temp_folder)
