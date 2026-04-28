# Step 3: Parse raw trace logs into per-CPU page-start address lists.

for subfigure_name in a b; do
    python3 py_scripts/process_trace.py $subfigure_name
done