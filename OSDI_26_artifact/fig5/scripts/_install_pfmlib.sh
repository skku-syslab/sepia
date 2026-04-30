set -e

rm -rf tools/libpfm
git clone https://github.com/wcohen/libpfm4.git tools/libpfm
cd tools/libpfm
echo "Start Make"
make > /dev/null 2>&1
echo "End Make"
cd examples
./showevtinfo > event_info.txt

echo "PMU event list saved to tools/libpfm/examples/event_info.txt"