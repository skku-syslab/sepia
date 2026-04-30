# Step 2: Prepare (or regenerate) the Tetris dataset.
#
# The default artifact flow uses the shipped `dummy_data/` directory and copies
# it into `data/`.

# ----------- Mock (pre-generated) tetris data -----------
# For artifact evaluation, we ship a pre-generated dataset under `dummy_data/`.
# This command copies it into `data/` so the remaining steps can run.
cp -r ./dummy_data/tetris_data-0x101500000-44 ./data
python3 py_scripts/make_page_index_table.py

# ----------- Real (re-generate) tetris data -----------
# Uncomment the following lines if you want to regenerate the dataset from
# scratch (this is typically slower and may require additional privileges).
# python3 py_scripts/make_page_index_table.py

# ./scripts/_create_tetris_blocks.sh <start_group> <end_group>
# ./scripts/_create_page_index_sequence.sh