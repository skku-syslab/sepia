# The implementation here is based on:
# John D. McCalpin. Mapping addresses to L3/CHA slices in Intel processors. 2021.
# See also: https://github.com/jdmccalpin/Intel_Address_Hash

# Step 0: Compile tools
# g++ -O3 -o ./bin/slice_map_extractor.bin ./code/slice_map_extractor.cpp \
#     -I./tools/libpfm/include \
#     ./tools/libpfm/lib/libpfm.a
g++ -O3 -o ./bin/gen_dummy_slice_map.bin ./code/gen_dummy_slice_map.cpp

# Step 1: Extract the slice map
# ./bin/slice_map_extractor.bin  # Real extractor — takes a long time; skipped in artifact
taskset -c 0 sudo ./bin/gen_dummy_slice_map.bin    # Dummy extractor — generates a synthetic mapping using the already-reversed hash function

# Step 2: Reverse-engineer the hash function from the slice map
python3 py_scripts/extract_hash_function.py