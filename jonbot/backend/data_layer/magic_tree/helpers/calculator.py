from typing import List
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from jonbot.backend.data_layer.magic_tree import MagicTreeDict


class TreeCalculator:
    def __init__(self, tree: 'MagicTreeDict'):
        self.tree = tree

    def calculate_stats(self,
                        metrics: List[str] = None,
                        data_keys: List[str] = None) -> 'MagicTreeDict':
        """
        Calculates the mean and standard deviation of all leaf nodes in the tree.

        If `add_leaves` is True, then the calculated stats are added to the existing tree.

        If `add_leaves` is False, then the calculated stats are returned in a new tree.

        :param metrics: list of metrics to calculate. Options are 'mean' and 'std'
        :param data_keys: list of data keys to calculate stats for. If 'ALL', then all data names are used
        """
        metrics = metrics or ['mean', 'std']
        data_keys = data_keys or ['ALL']

        stats_tree = self.tree.create_new()

        leaf_paths = self.tree.get_leaf_paths()
        for path in leaf_paths:
            leaf_orig = self.tree.data_from_path(path)
            data_name = path[-1]

            if isinstance(leaf_orig, list) and (data_name in data_keys or data_keys == ['ALL']):
                if 'mean' in metrics:
                    leaf_mean = np.mean(leaf_orig)
                    stats_tree[path]['mean'] = leaf_mean

                if 'std' in metrics:
                    leaf_std = np.std(leaf_orig)
                    stats_tree[path]['std'] = leaf_std
        return stats_tree
