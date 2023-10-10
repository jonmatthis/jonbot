from typing import TYPE_CHECKING
from typing import Union, List

import rich.tree
from rich.console import Console
from rich.tree import Tree
from tabulate import tabulate

if TYPE_CHECKING:
    from jonbot.backend.data_layer.magic_tree import MagicTreeDict


class TreePrinter:
    def __init__(self, tree: 'MagicTreeDict'):
        self.tree = tree

    def __str__(self):
        try:
            console = Console()
            with console.capture() as capture:
                rich_tree = Tree(":seedling:")
                self._add_branch(rich_tree, dict(self.tree))
                console.print(rich_tree)
            return capture.get()
        except Exception as e:
            print(f"Failed to print tree: {e}")
            raise e

    def _add_branch(self, rich_tree: rich.tree.Tree, subdict):
        try:
            for key, value in subdict.items():
                if isinstance(value, dict):
                    branch = rich_tree.add(str(key))
                    self._add_branch(branch, value)
                else:
                    value = str(value)  # try to convert it to a string
                    rich_tree.add(f"{key}: {value}")
        except Exception as e:
            print(f"Failed to add branch: {e}")
            raise e

    def print_table(self, leaf_keys: Union[str, List[str]]):
        df = self.tree.to_dataframe(leaf_keys=leaf_keys)
        print(tabulate(df, headers='keys', tablefmt='psql'))

    def to_dataframe(self, leaf_keys: Union[str, List[str]] = None):
        if leaf_keys is None:
            leaf_keys = self.tree.get_all_leaf_keys()

        paths = [self.tree.get_paths_to_keys(key=key) for key in leaf_keys]
        paths = [path for sublist in paths for path in sublist]  # flatten list

        table_dict = {}
        leaf_lengths = set()

        for path in paths:
            data = self.tree.get_data_from_path(path)
            if hasattr(data, '__iter__'):
                leaf_lengths.add(len(data))
            else:
                leaf_lengths.add(1)

            if tuple(path) in table_dict:
                raise ValueError(
                    f"Error at path level {path} - Path is not unique. Ensure each path in your tree is unique - exisiting paths: {table_dict.keys()}")
            table_dict[tuple(path)] = data

        if len(leaf_lengths) > 1:
            raise ValueError(
                f"Error at {path} level -  Leaf node data lengths are inconsistent. Ensure all leaf data have the same length or are scalar. Found lengths: {leaf_lengths}")

        return pd.DataFrame.from_dict(table_dict, orient='index').transpose()
