import datetime
import logging
import os
import subprocess
from pathlib import Path
import platform

from pydantic import BaseModel
from typing import List, Optional, Literal
import ast

logger  = logging.getLogger(__name__)

class QuineConfig(BaseModel):
    base_directory: str
    excluded_directories: List[str]
    included_extensions: List[str]
    excluded_file_names: List[str]
    print_content_for: List[str]
    print_mode: Literal["editor", "terminal", "both"] = "both"
    output_file_name: Optional[str] = f"quine_{datetime.datetime.now().isoformat().replace(':', '-')}.md"
    output_directory: str = str(Path(__file__).parent / "quine_output")

    def output_file_path(self) -> str:
        Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        return str(Path(self.output_directory) / self.output_file_name)



class StructurePrinter:
    def __init__(self, config: QuineConfig):
        self.config = config

    def _parse_file(self, file_path: str) -> List[str]:
        """
        Parse the Python file to extract classes, functions, and constants.

        Args:
            file_path (str): Path to the file to parse.

        Returns:
            List[str]: List of entity names in the file.
        """
        with open(file_path, 'r') as file:
            node = ast.parse(file.read())

        entities = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                entities.append(f"Function: {item.name}")
            elif isinstance(item, ast.ClassDef):
                entities.append(f"Class: {item.name}")
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        entities.append(f"Constant: {target.id}")

        return entities

    def print_structure(self):
        """
        Print the structure of the package based on the configuration.
        """
        for root_directory, directories, files in os.walk(self.config.base_directory):
            directories[:] = [d for d in directories if d not in self.config.excluded_directories]

            # Print directory name
            print(f"Directory: {root_directory}")

            for file_name in files:
                if file_name in self.config.excluded_file_names:
                    continue
                if any(file_name.endswith(extension) for extension in self.config.included_extensions):
                    file_path = os.path.join(root_directory, file_name)
                    entities = self._parse_file(file_path)
                    print(f"  File: {file_name}")
                    for entity in entities:
                        print(f"    {entity}")


class ContentPrinter:
    def __init__(self, config: QuineConfig):
        self.config = config


    def open_file(self) -> None:
        """Opens the generated file in the system's default program associated with the file's type."""
        current_os = platform.system()  # Get the current operating system

        try:
            if current_os == "Windows":
                os.startfile(self.config.output_file_path())
            elif current_os == "Darwin":  # MacOS
                subprocess.run(("open", self.config.output_file_path()), check=True)
            elif current_os == "Linux":
                subprocess.run(("xdg-open", self.config.output_file_path()), check=True)
            else:
                print(f"Unsupported operating system: {current_os}")
        except Exception as e:
            print(f"Failed to open the file: {e}")

    def print_content(self):
        for content_path in self.config.print_content_for:
            if os.path.isdir(content_path):
                # If the provided path is a directory, iterate over all files in the directory
                for file_name in os.listdir(content_path):
                    file_path = os.path.join(content_path, file_name)
                    if file_path.endswith(tuple(self.config.included_extensions)):
                        self._print_file_content(file_path)
            else:
                self._print_file_content(content_path)

    def _print_file_content(self, file_path):
        try:
            with open(file_path, 'r') as file:
                content = file.read()

            if self.config.print_mode in ["terminal", "both"]:
                print(f"Content of {file_path}:\n{'='*40}\n")
                print(content)

            # Save the content to the specified output file
            with open(self.config.output_file_path(), 'w') as file:
                file.write(content)

            if self.config.print_mode in ["editor", "both"]:
                self.open_file()

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
class Quine:
    def __init__(self, config: QuineConfig):
        self.config = config
        self.structure_printer = StructurePrinter(config)
        self.content_printer = ContentPrinter(config)

    def generate(self):
        self.structure_printer.print_structure()
        self.content_printer.print_content()


if __name__ == "__main__":
    base_directory_in = r"C:\Users\jonma\github_repos\jonmatthis\jonbot\jonbot\layer1_api_interface\api"
    quine_config = QuineConfig(
        base_directory=base_directory_in,
        excluded_directories=["__pycache__", ".git", "legacy"],
        included_extensions=[".py"],
        excluded_file_names=["poetry.lock", ".gitignore", "LICENSE"],
        print_content_for=[r"C:\Users\jonma\github_repos\jonmatthis\jonbot\utilities\quine.py"]
    )
    quine = Quine(quine_config)
    quine.generate()
