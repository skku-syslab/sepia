# Step 3: Generate address lists for each access pattern.
#
# Outputs:
# - data/address_list-stride1/address_list.<workingset_kb>.csv
# - data/address_list-tetris/address_list.<workingset_kb>.csv
./scripts/_gen_stride1_address_list.sh
./scripts/_gen_tetris_address_list.sh