"""Figure 5 configuration.

These tables describe which CPUs correspond to each subfigure (flow count), and
the expected working-set size for that subfigure.
"""

cpu_ids_table = {
    "a": {0,},
    "b": {0, 2,},
}

# Working-set size (MiB) used when describing each subfigure.
working_set_size_MB_table = {
    "a": 22,
    "b": 38,
}