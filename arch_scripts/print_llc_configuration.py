import os
import glob
import sys

def print_llc_configuration():
    # 1. Determine the number of LLC slice-related uncore units.
    # Newer Intel mesh-based systems typically expose CHAs; older generations may expose CBoxes.
    cha_pattern = "/sys/bus/event_source/devices/uncore_cha_*"
    cbox_pattern = "/sys/bus/event_source/devices/uncore_cbox_*"

    cha_dirs = glob.glob(cha_pattern)
    cbox_dirs = glob.glob(cbox_pattern)

    num_slices = len(cha_dirs)
    slice_unit = "CHA"

    if num_slices == 0:
        num_slices = len(cbox_dirs)
        slice_unit = "CBox"

    if num_slices == 0:
        print(
            "Error: Could not find uncore CHA/CBox perf event source directories (uncore_cha_* or uncore_cbox_*).",
            file=sys.stderr,
        )
        print(
            "Please verify that Intel uncore PMU support is available and exposed under /sys/bus/event_source/devices/.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Read basic LLC (L3 cache) info (using CPU 0)
    # On Intel systems: index0=L1D, index1=L1I, index2=L2, index3=L3 (LLC)
    l3_cache_dir = "/sys/devices/system/cpu/cpu0/cache/index3"

    try:
        # Read ways of associativity
        with open(os.path.join(l3_cache_dir, "ways_of_associativity"), "r") as f:
            ways = int(f.read().strip())

        # Read total number of sets (the total sets reported by CPUID)
        with open(os.path.join(l3_cache_dir, "number_of_sets"), "r") as f:
            total_sets = int(f.read().strip())

    except FileNotFoundError as e:
        print(f"Error: Unable to read cache information. ({e})", file=sys.stderr)
        sys.exit(1)

    # 3. Compute sets per slice
    # Divide the total sets from CPUID leaf 4 by the number of slices
    if total_sets % num_slices != 0:
        print("Warning: Total number of sets is not evenly divisible by the number of slices.")

    sets_per_slice = total_sets // num_slices

    # Page groups (4 KiB page coloring): pages in the same group share the same set-index bits.
    # With 4 KiB pages and 64 B cache lines, one page spans 4096/64 = 64 cache-line offsets,
    # so we divide the per-slice set count by 64 to get the number of page groups.
    page_groups = sets_per_slice // 64

    # Print the results
    print("="*40)
    print(" LLC (Last Level Cache) Configuration")
    print("="*40)
    print(f" Number of LLC Slices ({slice_unit:<4}) : {num_slices}")
    print(f" Ways of Associativity       : {ways}")
    print(f" Sets per Slice              : {sets_per_slice}")
    print(f" Page Groups                 : {page_groups}")
    print("="*40)

if __name__ == "__main__":
    print_llc_configuration()