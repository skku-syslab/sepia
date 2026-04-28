# Build the default-address generator (requires root at runtime due to pagemap).
g++ -O3 -o ./bin/gen_default_address_list.exe ./code/gen_default_address_list.cpp

# Generate address lists for each access pattern.
./scripts/_gen_default_address_list.sh
./scripts/_gen_stride1_address_list.sh
./scripts/_gen_tetris_address_list.sh