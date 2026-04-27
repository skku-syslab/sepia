set -e

# Step 0: Compile tools
g++ -O3 -o ./bin/analyze_by_sliding.bin ./code/analyze_by_sliding.cpp -I .

for subfigure_name in a b; do
    ./bin/analyze_by_sliding.bin $subfigure_name &
done

wait
echo Done