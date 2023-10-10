import collections
import sys
from collections import defaultdict
from typing import Any, Callable, Hashable, Iterable, Literal
from typing import List, Union

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
    def create_nested_dict() -> defaultdict:
        return defaultdict(MagicTreeDict.create_nested_dict)

    @property
    def number_of_leaves(self) -> int:
        return len(self.get_all_leaf_paths())

    @property
    def total_number_of_nodes(self) -> int:
        return len(self.get_all_paths())

    def get_all_leaf_paths(self) -> List[List[Hashable]]:
        """
        Returns a list of all the paths to the leaves in the tree.
        """
        leaf_paths = []
        self._traverse_tree(lambda path, value: leaf_paths.append(path))
        return leaf_paths

    def get_all_leaf_keys(self) -> List[Hashable]:
        """
        Returns all the keys of leaf nodes in the tree.
        """
        leaf_keys = []
        self._traverse_tree(lambda path, value: leaf_keys.append(path[-1]))
        return leaf_keys

    def get_paths_to_keys(self,
                          keys: Union[Hashable, Iterable[Hashable]],
                          duplicates_ok: bool = True,
                          missing_ok: bool = False) -> Union[List[Hashable], List[List[Hashable]]]:
        """
        Returns the paths to leaves/node(s) with the given key or keys.
        """
        if isinstance(keys, Hashable):
            keys = [keys]
        elif isinstance(keys, Iterable):
            keys = keys
        else:
            raise TypeError(f"Invalid key type: {type(keys)}")

        paths = []

        for key in keys:

            key_paths = self._traverse_tree(lambda path, value: key_paths.append(path) if path[-1] == key else None)

            if not key_paths and not missing_ok:
                raise KeyError(f"Leaf key '{key}' not found in tree.")
            if len(key_paths) > 1 and not duplicates_ok:
                raise KeyError(f"Leaf key '{key}' found multiple times in tree and `duplicates_ok` is set to False.")

            paths += key_paths

        return paths

    def get_data_from_path(self, path: Iterable[Hashable], current=None, missing_ok=True) -> Union[
        'MagicTreeDict', Any]:
        """
        Returns the data at the given path, be it a leaf(endpoint) or a branch (i.e. a sub-tree/dict)

        Either returns the data at the given path, or creates a new empty sub-tree dictionary at that location and returns that

        """
        if current is None:
            current = self
        data = current if len(path) == 0 else self.get_data_from_path(path[1:], current=current[path[0]])
        if not data and not missing_ok:
            raise KeyError(f"No data found at path: {path}")
        return data

    def calculate_tree_stats(self,
                             metrics: List[str] = None,
                             data_keys: List[str] = None) -> 'MagicTreeDict':
        stats = TreeCalculator(self).calculate_stats(metrics=metrics,
                                                     data_keys=data_keys)
        return stats

    def print_leaf_info(self, current=None, path=None) -> None:
        """Prints the information about all the leaves of the tree."""
        self._get_leaf_info()
        print(self._leaf_info)

    def print_table(self, keys: Union[str, List[str]] = None) -> None:
        if isinstance(keys, str):
            keys = [keys]
        TreePrinter(tree=self).print_table(keys)

    def get_all_paths(self) -> List[List[Hashable]]:
        """
        Returns a list of all the paths in the tree.
        """
        paths = []
        self._traverse_tree(lambda path, value: paths.append(path))
        return paths

    def filter_tree(self, target_key) -> 'MagicTreeDict':
        """
        Returns a new tree containing only the branches and leaves that contain the target key.
        """
        new_tree = MagicTreeDict()
        paths = self.get_paths_for_keys(keys=[target_key])
        if len(paths) == 0:
            raise KeyError(f"'{target_key}' not found in tree...")

        for path in paths:
            new_tree[path] = self.get_data_from_path(path)

        return new_tree

    def to_dataframe(self, leaf_keys: Union[str, List[str]] = None) -> 'pd.DataFrame':
        return TreePrinter(self).to_dataframe(leaf_keys=leaf_keys)

    def map_function(self,
                     function: Callable,
                     make_new_tree: bool = True,
                     **kwargs) -> "MagicTreeDict":
        results = TreeCalculator(self).map_function(function=function,
                                                    **kwargs)
        if not make_new_tree:
            self.update(results)
            return self
        return results

    def update(self,
               value: Any = None,
               level: Union[int, str, Iterable[Hashable]] = 0,
               duplicate_keys: Literal['error', 'overwrite', 'append'] = 'error') -> None:
        """
        Override the default update method to allow for updating the tree with different types:
        - If input is a dict, it updates the tree with the dict using key-value pairs.
            - if keys are not iterable, it inputs the data at the level specified by `level`
                - Level - 0 is the root/top level, -1 is the at the node that matches the key with duplicates handled according to `duplicate_keys`)
            - if keys are iterable, it inputs the data at the path specified by `keys` (with duplicates handled according to `duplicate_keys`)
        - If input is a list, it updates the tree with the list using index-value pairs.

        :return:
        """
        if isinstance(value, dict):
            if isinstance(level, int):
                if level == 0:
                    super().update(value)
                else:
                    raise ValueError(f"Invalid level: {level}")
            else:
                if isinstance(level, Hashable):
                    level = [level]
                elif not isinstance(level, Iterable):
                    raise TypeError(f"Invalid level type: {type(level)}")

                for key, value in value.items():
                    if isinstance(key, str):
                        key = [key]
                    elif not isinstance(key, Iterable):
                        raise TypeError(f"Invalid key type: {type(key)}")

                    if len(key) != len(level):
                        raise ValueError(f"Key and level must be the same length: {len(key)} != {len(level)}")

                    path = level + key
                    data_at_path = self.get_data_from_path(path=path)
                    if len(data_at_path) > 0:
                        if duplicate_keys == 'error':
                            raise KeyError(
                                f"Data already exists at path: {path} - Existing data: {data_at_path} and `duplicate_keys` is set to 'error'")
                        elif duplicate_keys == 'overwrite':
                            self.get_data_from_path(path=path[:-1])[key] = value
                        elif duplicate_keys == 'append':
                            data_at_path.update(value, level=0, duplicate_keys='append')

    def create_new_tree(self) -> 'MagicTreeDict':
        """
        Utility method for creating a new MagicTreeDict object (to avoid having to import the class)

        Big Ouroboros energy

        :return:
        """
        return self.__new__(self.__class__)

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

    def __setitem__(self, key: Union[Hashable, Iterable[Hashable]], value: Any):
        """
        Allows for setting values using a list of keys, e.g. `magic_tree['a']['b']['c'] = 1`
        Checks if the input is a Hashable or an Iterable of Hashables (aka a tree path)
        """
        if isinstance(key, Hashable):
            super(MagicTreeDict, self).__setitem__(key, value)
        elif isinstance(key, Iterable):
            key = list(key)
            if not all(isinstance(k, Hashable) for k in key):
                raise TypeError("Invalid key/path type - all keys in a path must be hashable.")
            current_data = self
            current_data[key[:-1]][key[-1]] = value
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
