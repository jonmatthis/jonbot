import numpy as np

from jonbot.backend.data_layer.magic_tree import MagicTreeDict


def create_sample_magic_tree():
    magic_tree = MagicTreeDict()
    magic_tree['a']['b']['c']['woo'] = [1, 2, 13]
    magic_tree['a']['b']['c']['woo2'] = '✨'
    magic_tree['a']['b']['??️'] = np.eye(
        3)  # TODO - doesn't handle this correctly - skips it in stats, and prints matrix poorly
    magic_tree['a']['c']['bang'] = [4, 51, 6]
    magic_tree['a']['b']['c']['hey'] = [71, 8, 9]

    return magic_tree


def magic_tree_demo():
    tree = create_sample_magic_tree()
    print(f"Print as regular dict:\n")
    print(tree.__dict__())
    print(dict(
        tree))  # TODO - this still includes the defaultdicts, will need to override __iter__ or items or soemthing to fix this ish

    print(f"Original MagicTreeDict:\n{tree}\n\n")
    print(f"Calculate tree stats and return in new MagicTreeDict:\n{tree.calculate_tree_stats()}\n\n")
    print(f"Print Table:\n")
    tree.print_table(['woo', 'bang', 'hey'])

    print(f"Filter tree on `c`:\n")
    c_tree = tree.filter_tree('c')
    print(c_tree)

    stats = tree.calculate_tree_stats()
    print(f"Calculate Tree Stats:\n{stats}\n\n")
    print(f"Print stats table:\n")
    stats.print_table(['mean', 'std'])
    return tree


if __name__ == "__main__":
    tree = magic_tree_demo()
    f = 9
