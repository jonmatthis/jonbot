import collections
import sys
from collections import defaultdict
from typing import Any
from typing import List, Union

import pandas as pd
from rich.console import Console
from rich.tree import Tree

from jonbot.backend.data_layer.magic_tree.helpers.calculator import TreeCalculator
from jonbot.backend.data_layer.magic_tree.helpers.printer import TreePrinter


class MagicTreeDict(defaultdict):
    """
    A class that integrates `defaultdict` with added functionality.

    The `MagicTreeDict` class allows for representing a nested dictionary
    in a tree-like structure. It provides methods for traversing the tree,
    and getting or setting data using a list of keys, and also calculates stats
    and prints information about the leaves.
    """

    def __init__(self):
        super().__init__(self.create_nested_dict)

    @staticmethod
    def create_nested_dict():
        return defaultdict(MagicTreeDict.create_nested_dict)

    def get_leaf_paths(self):
        """
        Returns a list of all the paths to the leaves in the tree.
        """
        leaf_paths = []
        self._traverse_tree(lambda path, value: leaf_paths.append(path))
        return leaf_paths

    def get_leaf_keys(self):
        """
        Returns all the keys of leaf nodes in the tree.
        """
        leaf_keys = []
        self._traverse_tree(lambda path, value: leaf_keys.append(path[-1]))
        return leaf_keys

    def get_path_to_leaf(self, leaf_key: str) -> List[str]:
        """
        Returns the path to a specified leaf in the tree.
        """
        leaf_paths = []
        self._traverse_tree(lambda path, value: leaf_paths.append(path) if path[-1] == leaf_key else None)

        if not leaf_paths:
            raise KeyError(f"Leaf key '{leaf_key}' not found in tree.")

        return leaf_paths

    def data_from_path(self, path: List[str], current=None) -> Union['MagicTreeDict', Any]:
        """
        Returns the data at the given path, be it a leaf(endpoint) or a branch (i.e. a sub-tree/dict)

        Either returns the data at the given path, or creates a new empty sub-tree dictionary at that location and returns that

        """
        if current is None:
            current = self
        return current if len(path) == 0 else self.data_from_path(path[1:], current=current[path[0]])

    def calculate_tree_stats(self,
                             metrics: List[str] = None,
                             data_keys: List[str] = None) -> 'MagicTreeDict':
        stats = TreeCalculator(self).calculate_stats(metrics=metrics,
                                                     data_keys=data_keys)
        return stats

    def print_leaf_info(self, current=None, path=None):
        """Prints the information about all the leaves of the tree."""
        console = Console()
        tree = Tree(":seedling:")
        self._get_leaf_info()
        print(self._leaf_info)

    def print_table(self, keys: Union[str, List[str]] = None):
        if isinstance(keys, str):
            keys = [keys]
        TreePrinter(tree=self).print_table(keys)

    def get_paths_for_keys(self, keys):
        paths = []
        self._traverse_tree(lambda path, value: paths.append(path) if path[-1] in keys else None)
        return paths

    def filter_tree(self, target_key, current=None, path=None):
        """
        Returns a new tree containing only the branches and leaves that contain the target key.
        """
        new_tree = MagicTreeDict()
        paths = self.get_paths_for_keys(keys=[target_key])
        if len(paths) == 0:
            raise KeyError(f"'{target_key}' not found in tree...")

        for path in paths:
            new_tree[path] = self.data_from_path(path)

        return new_tree

    def to_dataframe(self, leaf_keys: Union[str, List[str]] = None):
        if leaf_keys is None:
            leaf_keys = self.get_leaf_keys()

        paths = [self.get_path_to_leaf(leaf_key=key) for key in leaf_keys]
        paths = [path for sublist in paths for path in sublist]  # flatten list

        table_dict = {}
        leaf_lengths = set()

        for path in paths:
            data = self.data_from_path(path)
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

    @staticmethod
    def create_new() -> 'MagicTreeDict':
        """
        Utility method for creating a new MagicTreeDict object (to avoid having to import the class)
        :return:
        """
        return MagicTreeDict()

    def _get_leaf_info(self, current=None, path=None):
        if current is None:
            self._leaf_info = MagicTreeDict()
            current = self
        if path is None:
            path = []
        for key, value in current.items():
            new_path = path + [key]

            type_ = type(value).__name__
            info = str(value)[:20] + (str(value)[20:] and '..')
            nbytes = sys.getsizeof(value)
            memory_address = hex(id(value))

            if isinstance(value, defaultdict):
                self._get_leaf_info(current=value,
                                    path=new_path)
            else:
                self._leaf_info[new_path].update({"type": type_,
                                                  "info": info,
                                                  "nbytes": nbytes,
                                                  "memory_address": memory_address})

    def _traverse_tree(self, callback, current=None, path=None):
        if current is None:
            current = self
        if path is None:
            path = []
        for key, value in current.items():
            new_path = path + [key]
            callback(new_path, value)
            if isinstance(value, defaultdict):
                self._traverse_tree(callback, value, new_path)

    def __str__(self):
        return TreePrinter(self).__str__()

    def __setitem__(self, keys, value):
        """
        Allows for setting values using a list of keys, e.g. `magic_tree['a']['b']['c'] = 1`
        Checks if the input is a string, an integer, or an iterable.
        If it's a string or integer, it just sets the value at the given key, like a normal dict.
        If it's an iterable, it builds a path out of it and sets the value at that path.
        """
        if isinstance(keys, str) or isinstance(keys, int):
            super(MagicTreeDict, self).__setitem__(keys, value)
        elif isinstance(keys, collections.abc.Iterable):
            current_data = self
            for key in keys[:-1]:
                current_data = current_data[key]
            current_data[keys[-1]] = value
        else:
            raise TypeError("Invalid key type.")

    def __getitem__(self, keys):
        """
        Allows for getting values using a list of keys, e.g. `magic_tree['a']['b']['c']`
        Checks if the input is a string, an integer, or an iterable.
        If it's a string or integer, it just gets the value at the given key, like a normal dict.
        If it's an iterable, it builds a path out of it and gets the value at that path.

        """
        if isinstance(keys, str) or isinstance(keys, int):
            return super(MagicTreeDict, self).__getitem__(keys)
        elif isinstance(keys, collections.abc.Iterable):
            current_data = self
            for key in keys:
                current_data = current_data[key]
            return current_data
        else:
            raise TypeError("Invalid key type.")

    def __dict__(self):
        def convert(default_dict):
            if isinstance(default_dict, defaultdict):
                default_dict = {k: convert(v) for k, v in default_dict.items()}
            return default_dict

        return convert(self)
