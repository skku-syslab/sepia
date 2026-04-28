"""Figure 9 configuration.

This file centralizes constants used by the address-list generators and the
"tetris" page-selection scripts.

All values are treated as constants and imported by other scripts.
"""

# User-chosen physical base address used to build synthetic physical address
# lists (one cache line every 64B) in the Python generators.
START_ADDRESS_HEX   = "0x101500000"
START_ADDRESS_INT   = int(START_ADDRESS_HEX, 16)
ADDRESS_RANGE       = 512 * (1<<20) # bytes (512 MiB)

# LLC model parameters used by the miss-rate estimator.
N_SETS              = 64
N_WAYS              = 12
N_SLICES            = 26
# Page-grouping derived from the total number of sets:
#   2048 sets = (64 sets per 4KiB page) * (32 page groups)
# In this codebase, the full set index is modeled as:
#   TOTAL_SETS = N_SETS * NUM_PAGE_GROUPS
NUM_PAGE_GROUPS     = 32

# Target unit size used by the "tetris" construction (per page group).
# Total pages across all groups is `TARGET_UNIT_PAGES * NUM_PAGE_GROUPS`.
# With the default values: 272 * 32 = 8,704 pages = 34,816 KiB (~34 MiB).
TARGET_UNIT_PAGES   = 272

# Occupancy threshold in the per-(set,slice) counter beyond which accesses are
# considered "spilling" (violating the modeled associativity).
THRESHOLD           = 12     # number of full LLC ways