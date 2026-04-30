# Step 0: Setup the output directory.
mkdir -p data/address_list-tetris

# Step 1: Generate the address list.
bash -c '
for workingset_size_mb in 16 18 20 22 24 26 28 30 32 34 36; do
    echo "Stride-1 ${workingset_size_mb}MB start"
    python3 py_scripts/gen_tetris_address_list.py $workingset_size_mb > /dev/null 2>&1 &
done
wait
'

wait
echo Done