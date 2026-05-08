g++ -O3 -o ./tools/measure_dram_traffic.bin ./tools/measure_dram_traffic.cpp \
    -I./tools/libpfm/include \
    ./tools/libpfm/lib/libpfm.a