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


if __name__ == "__main__":
    magic_tree_demo()

# # Expected output (2023-10-08):
# Original MagicTreeDict:
# 🌱
# └── a
#     ├── b
#     │   ├── c
#     │   │   ├── woo: [1, 2, 13]
#     │   │   ├── woo2: ✨
#     │   │   └── hey: [71, 8, 9]
#     │   └── ??️: [[1. 0. 0.]
#     │        [0. 1. 0.]
#     │        [0. 0. 1.]]
#     └── c
#         └── bang: [4, 51, 6]
#
#
#
# Calculate tree stats and return in new MagicTreeDict:
# 🌱
# └── a
#     ├── b
#     │   └── c
#     │       ├── woo
#     │       │   ├── mean: 5.333333333333333
#     │       │   └── std: 5.436502143433364
#     │       └── hey
#     │           ├── mean: 29.333333333333332
#     │           └── std: 29.465610840812758
#     └── c
#         └── bang
#             ├── mean: 20.333333333333332
#             └── std: 21.69997439834639
#
#
#
# Print Table:
#
# +----+--------------------------+----------------------+--------------------------+
# |    |   ('a', 'b', 'c', 'woo') |   ('a', 'c', 'bang') |   ('a', 'b', 'c', 'hey') |
# |----+--------------------------+----------------------+--------------------------|
# |  0 |                        1 |                    4 |                       71 |
# |  1 |                        2 |                   51 |                        8 |
# |  2 |                       13 |                    6 |                        9 |
# +----+--------------------------+----------------------+--------------------------+
# Calculate Tree Stats:
# 🌱
# └── a
#     ├── b
#     │   └── c
#     │       ├── woo
#     │       │   ├── mean: 5.333333333333333
#     │       │   └── std: 5.436502143433364
#     │       └── hey
#     │           ├── mean: 29.333333333333332
#     │           └── std: 29.465610840812758
#     └── c
#         └── bang
#             ├── mean: 20.333333333333332
#             └── std: 21.69997439834639
#
#
#
# Print stats table:
#
# +----+----------------------------------+----------------------------------+------------------------------+---------------------------------+---------------------------------+-----------------------------+
# |    |   ('a', 'b', 'c', 'woo', 'mean') |   ('a', 'b', 'c', 'hey', 'mean') |   ('a', 'c', 'bang', 'mean') |   ('a', 'b', 'c', 'woo', 'std') |   ('a', 'b', 'c', 'hey', 'std') |   ('a', 'c', 'bang', 'std') |
# |----+----------------------------------+----------------------------------+------------------------------+---------------------------------+---------------------------------+-----------------------------|
# |  0 |                          5.33333 |                          29.3333 |                      20.3333 |                          5.4365 |                         29.4656 |                        21.7 |
# +----+----------------------------------+----------------------------------+------------------------------+---------------------------------+---------------------------------+-----------------------------+
#
# Process finished with exit code 0
