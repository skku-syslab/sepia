"""Configuration for Figure 10 scripts.

These constants parameterize the (offline) address-pattern generation and the
miss/violation-rate model used to compare Stride-1 vs Tetris patterns.

All scripts assume they are executed from the Figure 10 directory so that
relative paths like `data/...` and `common/...` resolve correctly.
"""

START_ADDRESS_HEX   = "0x101500000"
START_ADDRESS_INT   = int(START_ADDRESS_HEX, 16)
ADDRESS_RANGE       = 4 * (1<<30) # 4 GiB region used to build the page-index table

N_SETS              = 64  # Cache lines per 4KiB page (4096 / 64)
N_WAYS              = 12
N_SLICES            = 26
NUM_PAGE_GROUPS     = 32  # Page groups (= page_index mod NUM_PAGE_GROUPS)

TARGET_UNIT_PAGES   = 44   # Pages per group (44 * 32 groups * 4KiB = 5.5MiB)
THRESHOLD           = 2    # Modeled DDIO allocation: number of LLC ways