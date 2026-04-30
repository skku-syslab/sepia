set -e

# Step 1: Install libpfm and allocate 1GiB huge pages used by the slice-map
# extractor.

./scripts/_install_pfmlib.sh

expect_num_hugepages=5 # 5GiB (1GiB huge pages)
echo $expect_num_hugepages | sudo tee /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages > /dev/null

actual_num_hugepages=$(cat /sys/kernel/mm/hugepages/hugepages-1048576kB/nr_hugepages)
if [ "$actual_num_hugepages" -ne "$expect_num_hugepages" ]; then
    echo "WARNING: Expected $expect_num_hugepages hugepages, but got $actual_num_hugepages." >&2
    echo "WARNING: Check if the system has enough memory." >&2
fi

mkdir -p outputs data tools bin traces plots