from typing import TYPE_CHECKING, Union, Literal, Hashable, Callable, Any, Iterable, List

from jonbot import logger

if TYPE_CHECKING:
    from jonbot.backend.data_layer.magic_tree import MagicTreeDict


class TreeCalculator:
    def __init__(self, tree: 'MagicTreeDict'):
        self.tree = tree

    def map_function(self,
                     function: Callable[[Any], Any],
                     map_to: Union[Literal['leaves', 'nodes', 'all-bottom-up', 'all-top-down'],  # mode
                     Union[Hashable, Iterable[Hashable]],  # key(s)
                     Union[Iterable[Hashable], Iterable[Iterable[Hashable]]]] = 'leaves',  # path(s)
                     pre_formatter: Callable[[Any], Any] = None,
                     post_formatter: Callable[[Any], Any] = None,
                     iterate_function_application: bool = False,
                     ):
        """
        Applies a function to specified parts of the tree.
        :param function: The function to apply to the leaves - must take a single argument (the leaf's value).
        :param map_to: Specifies which part of the tree the function will be applied to. Can be one of:
            - 'leaves' - apply to all leaves
            - 'nodes' - apply to all nodes (excluding leaves)
            - 'all-bottom-up' - apply to all nodes and leaves, starting from the bottom of the tree and working up
            - 'all-top-down' - apply to all nodes and leaves, starting from the top/root of the tree and working down
            - a key or iterable of keys: (Type: Union[Hashable, Iterable[Hashable]) Specifies which keys to apply the function to (using `self.tree.get_paths_to_key(key)`)
            - A path or iterable of paths (Type: Union[Hashable, Iterable[Hashable]]) to apply the function to (e.g. ['a', 'b', 'c'] will apply the function to the leaf with path 'a/b/c')
        :param pre_formatter: A function to apply to the leaf/node's value BEFORE applying the function (if this returns "None", the function will not be applied to this leaf).
        :param post_formatter: A function to apply to the leaf's value AFTER applying the function.
        :param iterate_function_application: Whether to iterate the function application over the leaf's value (if it is an iterable).
        :return:
        """
        results = self.tree.create_new_tree()

        paths = self._get_paths_to_map_to(map_to)
        for path in paths:
            og_value = self.tree.get_data_from_path(path)
            # Make sure the value to operate on is a list
            og_values = [og_value] if iterate_function_application else [og_value, ]

            if pre_formatter:
                values_to_apply_function_to = [pre_formatter(item) for item in og_values]
            else:
                values_to_apply_function_to = og_values
            new_values = []
            for item in values_to_apply_function_to:
                try:
                    new_value = function(item)
                except Exception as e:
                    logger.error(f"Error applying function to item: {item} - {e}")
                    logger.exception(e)
                    logger.info(f"Skipping this item!")
                    pass

            if post_formatter:
                output_values = [post_formatter(item) for item in new_values]
            else:
                output_values = new_values

            # Unpack the list if not in iterate_function_application mode
            results[path] = output_values
        return results

    def _get_paths_to_map_to(self, map_to) -> List[List[Hashable]]:
        """
        Gets the paths to apply the function to, based on the `map_to` parameter (see `map_to_leaves` for details).
        :param map_to:
        :return: paths
        """
        paths = []
        try:
            if isinstance(map_to, Hashable):
                if map_to == 'leaves':
                    paths = self.tree.get_all_leaf_paths()
                elif map_to == 'nodes':
                    paths = self.tree.get_all_paths()
                    paths = [path[:-1] for path in paths if len(path) > 0]
                elif map_to == 'all-bottom-up':
                    paths = self.tree.get_all_paths()
                    # sort by length -  longest paths are first
                    paths = sorted(paths, key=lambda path: len(path), reverse=True)
                elif map_to == 'all-top-down':
                    paths = self.tree.get_all_paths()
                    # sort by length - shortest paths are first
                    paths = sorted(paths, key=lambda path: len(path))
                else:
                    paths = self.tree.get_paths_to_keys(keys=map_to, duplicates_ok=True, missing_ok=False)

            elif isinstance(map_to, Iterable):
                for item in map_to:
                    if isinstance(item, Hashable):
                        paths += self.tree.get_paths_to_keys(keys=item, duplicates_ok=True, missing_ok=False)
                    elif isinstance(item, Iterable):
                        for subitem in item:
                            if isinstance(subitem, Hashable):
                                paths.append(item)
                            else:
                                raise ValueError(
                                    f"A subitem in the map_to iterable is not hashable: map_to - {item}, problematic subitem - {subitem}")
                    else:
                        raise ValueError(f"Invalid type for item in map_to: {type(item)}")
            else:
                raise ValueError(f"Invalid type for map_to: {type(map_to)}")
            if len(paths) == 0:
                raise ValueError(f"No paths found for map_to: {map_to}")
        except KeyError as e:
            logger.error(f"Key not found in tree: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error getting paths from tree: {e}")
            raise e

        return paths


if __name__ == "__main__":
    from jonbot.backend.data_layer.magic_tree import MagicTreeDict

    import numpy as np

    tree = MagicTreeDict()
    tree["a"]["b"]["c"] = [1, 2, 3]
    tree[["a", "b", 3]] = [4, 5, 6]
    tree[("a", "c", "a")] = [4, 5, 6]
    print(tree)
    mean_tree = tree.map_function(function=np.mean,
                                  map_to='leaves', )
    print(mean_tree)
