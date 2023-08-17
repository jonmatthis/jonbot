from pathlib import Path
from typing import List


def get_bot_config_toml_path(bot_nick_name:str) -> List[str]:
    target_toml = f"{bot_nick_name}_config.toml"

    current_directory = Path(__file__).parent
    toml_files = [str(file) for file in current_directory.glob("*.toml")]

    if not toml_files:
        raise FileNotFoundError("No TOML files found in this directory!")

    for toml_file in toml_files:
        if Path(toml_file).name == target_toml:
            return [toml_file]

    raise FileNotFoundError(f"No TOML file named {target_toml} found in this directory!")


if __name__ == "__main__":
    toml_files = get_bot_config_toml_path()
    print("TOML files in this directory:")
    for file in toml_files:
        print(file)
