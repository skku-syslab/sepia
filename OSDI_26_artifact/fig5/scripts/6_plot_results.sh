set -e

# Step 6: Plot per-subfigure results.

for subfigure_name in a b; do
    python3 py_scripts/plot_result.py $subfigure_name
done