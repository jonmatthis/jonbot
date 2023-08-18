import ast
import datetime
import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Literal

import pyperclip
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)

## MODEL DEFINITIONS
class ContentFetcherConfig(BaseModel):
    fetch_content_for: List[str] = Field([], description="List of files/folders to fetch content for")
    recursion_depth: int = Field(0,
                                 description="0 means it won't go into subdirectories, -1 means it will go into all subdirectories")


class StructureFetcherConfig(BaseModel):
    base_directory: str
    excluded_directories: List[str]
    included_extensions: List[str]
    excluded_file_names: List[str]
    content: ContentFetcherConfig  # Add ContentFetcherConfig to StructureFetcherConfig
    indent: int = 0


class QuineConfig(BaseModel):
    print_mode: Literal["file", "terminal", "clipboard", "all"]
    structure: StructureFetcherConfig
    content: ContentFetcherConfig
    output_file_name: str
    output_directory: str

    def output_file_path(self) -> str:
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        return str(Path(self.output_directory) / self.output_file_name)


# CORE PROCESSES
class StructureFetcher:
    def __init__(self, config: StructureFetcherConfig):
        self.config = config

    def _parse_file(self, file_path: str) -> dict:
        # Check if the file is in the list of files/folders to fetch content for
        if file_path not in self.config.content.fetch_content_for and not any(
                os.path.commonpath([file_path, content_path]) == content_path for content_path in
                self.config.content.fetch_content_for
        ):
            return {'functions': [], 'classes': [], 'constants': []}

        logger.debug(f"Reading file: {file_path}")  # TRACE level log
        with open(file_path, 'r', encoding='utf-8') as file:
            node = ast.parse(file.read())

        entities = {
            'functions': [],
            'classes': [],
            'constants': []
        }

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entities['functions'].append(f"{item.name}({','.join([arg.arg for arg in item.args.args])})")
            elif isinstance(item, ast.ClassDef):
                methods = [m.name for m in item.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                entities['classes'].append(f"{item.name}(init or constructor methods, {methods})")
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        entities['constants'].append(target.id)

        return entities

    def fetch_structure(self, indent=None) -> str:
        logger.debug(f"Fetching structure with base directory: {self.config.base_directory}")
        output = ""
        indent = indent if indent is not None else self.config.indent
        for root_directory, directories, files in os.walk(self.config.base_directory):
            directories[:] = [d for d in directories if d not in self.config.excluded_directories]
            ind = '| ' * indent
            output += f"{ind}| {os.path.basename(root_directory)}/\n"
            for file_name in files:
                if file_name in self.config.excluded_file_names:
                    continue
                if any(file_name.endswith(extension) for extension in self.config.included_extensions):
                    file_path = os.path.join(root_directory, file_name)
                    entities = self._parse_file(file_path)
                    output += f"{ind}|- {file_name}\n"
                    for entity_type, entity_list in entities.items():
                        if entity_list:
                            output += f"{ind}  |- {entity_type.capitalize()}: {', '.join(entity_list)}\n"

            for directory in directories:
                self.config.base_directory = os.path.join(root_directory, directory)
                output += self.fetch_structure(indent + 1)

        return output


class ContentFetcher:
    def __init__(self, config: ContentFetcherConfig):
        self.config = config

    def fetch_content(self, path=None, current_depth=0) -> str:
        if path is None:
            path = self.config.fetch_content_for

        output = ""

        # Check the recursion depth
        if self.config.recursion_depth != -1 and current_depth > self.config.recursion_depth:
            return output

        for content_path in path:
            if os.path.isdir(content_path):
                for file_name in os.listdir(content_path):
                    file_path = os.path.join(content_path, file_name)
                    # Check if it's a directory and we need to go deeper
                    if os.path.isdir(file_path):
                        output += self.fetch_content([file_path], current_depth + 1)
                    else:
                        output += self._get_file_content(file_path)
            else:
                output += self._get_file_content(content_path)
        return output

    def _get_file_content(self, file_path) -> str:
        logger.debug(f"Getting content for file: {file_path}")  # TRACE level log
        try:
            with open(file_path, 'r', encoding="utf-8") as file:
                content = file.read()
            return f"Content of {file_path}:\n{'=' * 40}\n{content}\n\n"
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ""


# MAIN DEFINITION
class Quine:
    def __init__(self, config: QuineConfig):
        self.config = config
        self.structure_fetcher = StructureFetcher(config.structure)
        self.content_fetcher = ContentFetcher(config.content)

    def generate(self):
        output = self.structure_fetcher.fetch_structure()
        output += "\n\n" + self.content_fetcher.fetch_content()

        logger.debug(f"Writing output to file: {self.config.output_file_path()}")
        with open(self.config.output_file_path(), 'w') as file:
            file.write(output)



        if self.config.print_mode in ["clipboard", "all"]:
            logger.debug("Copying output to clipboard")
            pyperclip.copy(output)


        if self.config.print_mode in ["file", "all"]:
            self.open_file()

        if self.config.print_mode in ["terminal", "all"]:
            logger.debug("Printing output to terminal\n\n")
            print(output)

    def open_file(self):
        current_os = platform.system()
        try:
            if current_os == "Windows":
                os.startfile(self.config.content.output_file_path())
            elif current_os == "Darwin":
                subprocess.run(("open", self.config.content.output_file_path()), check=True)
            elif current_os == "Linux":
                subprocess.run(("xdg-open", self.config.content.output_file_path()), check=True)
            else:
                print(f"Unsupported operating system: {current_os}")
        except Exception as e:
            print(f"Failed to open the file: {e}")


if __name__ == "__main__":
    base_directory_in = r"C:\Users\jonma\github_repos\jonmatthis\jonbot\scratchpad\api_streaming_test"

    quine_config = QuineConfig(
        print_mode="all",
        structure=StructureFetcherConfig(
            content=ContentFetcherConfig(
                fetch_content_for=[],
                recursion_depth=0,
            ),
            base_directory=base_directory_in,
            excluded_directories=["__pycache__", ".git", "legacy"],
            included_extensions=[".py"],
            excluded_file_names=["poetry.lock", ".gitignore", "LICENSE"],
        ),
        content=ContentFetcherConfig(
            fetch_content_for=[base_directory_in],
            recursion_depth=1,
        ),
        output_file_name=f"quine_{datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S.%f')}.txt",
        output_directory=str(Path(__file__).parent / "quine_output"),
    )

    quine = Quine(quine_config)
    quine.generate()
