# Generate Tetris address lists for several working-set sizes.

# Step 0: Setup the output directory.
mkdir -p data/address_list-tetris

# Step 1: Generate the address lists (in parallel).
bash -c '
for workingset_size_kb in 4096 5120 5632 6656; do
    echo "Stride-1 ${workingset_size_kb}kB start"
    python3 py_scripts/gen_tetris_address_list.py $workingset_size_kb > /dev/null 2>&1 &
done
wait
'

wait
echo Done