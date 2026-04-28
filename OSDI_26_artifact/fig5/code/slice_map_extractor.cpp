// Perf-based LLC slice mapping extractor (Figure 5).
//
// This program allocates a huge-page-backed buffer, probes addresses via a
// flush+reload loop, and attributes LLC lookup misses to each CHA (LLC slice)
// using uncore perf events. For each probed address it records (va, pa, slice)
// to a CSV file.
//
// Output:
//   outputs/slice_mapping.csv
//
// Notes:
// - This tool is hardware/OS dependent (uncore event names, number of slices,
//   perf permissions, huge page availability). The artifact pipeline typically
//   uses `gen_dummy_slice_map.cpp` instead of running this extractor.

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <csignal>

#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/mman.h>         // MAP_HUGE_1GB
#include <linux/perf_event.h>
#include <asm/unistd.h>
#include <emmintrin.h>

#include <perfmon/pfmlib.h>
#include <perfmon/pfmlib_perf_event.h>

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Number of LLC slices (CHA units) on this system
const int    N_SLICE  = 26;

// Buffer size: 4 GiB backed by 1 GiB huge pages (requires 4 huge pages)
const size_t BUF_SIZE = 4ULL << 30;

// Measurement stride.
// 64   = per cache line (fine-grained, slow: ~16M iterations)
// 4096 = per page       (fast: ~256K iterations, sufficient for slice mapping)
const size_t STRIDE   = 64;

// Flush+reload repetitions per address (more = less noise)
const int    N_REPS   = 10000;

// ---------------------------------------------------------------------------
// PMU event strings — one per CHA slice.
// Adjust these strings if libpfm uses different names on your system.
// ---------------------------------------------------------------------------
const char *names[N_SLICE] = {
    "icx_unc_cha0::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha1::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha2::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha3::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha4::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha5::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha6::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha7::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha8::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha9::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha10::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha11::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha12::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha13::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha14::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha15::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha16::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha17::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha18::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha19::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha20::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha21::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha22::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha23::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha24::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
    "icx_unc_cha25::UNC_CHA_LLC_LOOKUP:DATA_READ_MISS",
};

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------

pfm_perf_encode_arg_t encode;
perf_event_attr       pe;
std::vector<int>      fd_arr;
uint64_t             *Array;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

unsigned long long get_pagemap_entry(void *va) {
    unsigned long long result;
    static int pagemap_fd  = -1;
    static int initialized = 0;

    if (!initialized) {
        char filename[64];
        sprintf(filename, "/proc/%d/pagemap", getpid());
        pagemap_fd = open(filename, O_RDONLY);
        if (pagemap_fd < 0) {
            perror("open /proc/<pid>/pagemap failed");
            return 0ULL;
        }
        initialized = 1;
    }

    off_t offset = ((long long)va >> 12) << 3;
    if (pread(pagemap_fd, &result, 8, offset) != 8)
        return 0ULL;
    return result;
}

// Flush and reload `target` N_REPS times, then return the CHA slice index
// that recorded the most LLC data-read misses.
static int probe_slice(uint64_t *target) {
    for (int i = 0; i < N_SLICE; i++) {
        ioctl(fd_arr[i], PERF_EVENT_IOC_RESET,  0);
        ioctl(fd_arr[i], PERF_EVENT_IOC_ENABLE, 0);
    }

    for (int r = 0; r < N_REPS; r++) {
        asm volatile(
            "clflush (%0)\n\t"
            "mfence\n\t"
            "movq   (%0), %%r8\n\t"
            "mfence\n\t"
            :
            : "r" (target)
            : "memory", "r8"
        );
    }

    for (int i = 0; i < N_SLICE; i++)
        ioctl(fd_arr[i], PERF_EVENT_IOC_DISABLE, 0);

    int      max_slice = -1;
    uint64_t max_count = 0;
    int res;
    for (int i = 0; i < N_SLICE; i++) {
        uint64_t count = 0;
        res = read(fd_arr[i], &count, sizeof(uint64_t));
        if (count > max_count) {
            max_count = count;
            max_slice = i;
        }
    }
    return max_slice;
}

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------

int main(int argc, char **argv) {
    int ret;

    // -----------------------------------------------------------------------
    // 1. Initialize libpfm
    // -----------------------------------------------------------------------
    ret = pfm_initialize();
    if (ret != PFM_SUCCESS) {
        fprintf(stderr, "pfm_initialize failed: %s\n", pfm_strerror(ret));
        return EXIT_FAILURE;
    }

    // -----------------------------------------------------------------------
    // 2. Allocate a 4 GiB working buffer backed by 1 GiB huge pages
    // -----------------------------------------------------------------------
    Array = (uint64_t *)mmap(NULL, BUF_SIZE,
                              PROT_READ | PROT_WRITE,
                              MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB | MAP_HUGE_1GB,
                              -1, 0);
    if (Array == (uint64_t *)-1) {
        perror("mmap failed");
        return EXIT_FAILURE;
    }

    // Fault in every cache line so physical addresses are stable before probing
    const size_t n_lines = BUF_SIZE / 64;
    for (size_t i = 0; i < n_lines; i++)
        ((volatile uint64_t *)Array)[i<<3] = 0;

    // Log the physical address of the buffer base (to stderr so it doesn't
    // pollute the CSV written to stdout)
    {
        void *va = (void *)Array;
        unsigned long long pme = get_pagemap_entry(va);
        unsigned long long pfn = pme & ((1ULL << 55) - 1);
        unsigned long long pa  = (pfn << 12) | ((unsigned long long)va & 0xFFF);
        fprintf(stderr, "Array base: va=%p  pa=0x%012llx  pfn=0x%llx\n", va, pa, pfn);
    }

    // -----------------------------------------------------------------------
    // 3. Open one perf-event fd per CHA slice, pinned to cpu == slice index
    // -----------------------------------------------------------------------
    for (int i = 0; i < N_SLICE; i++) {
        memset(&pe, 0, sizeof(pe));
        pe.size           = sizeof(pe);
        pe.disabled       = 1;
        pe.exclude_kernel = 1;
        pe.exclude_hv     = 1;

        encode.attr = &pe;
        encode.fstr = (char **)&names[i];
        encode.size = sizeof(encode);

        ret = pfm_get_os_event_encoding(names[i], PFM_PLM3 | PFM_PLM0,
                                        PFM_OS_PERF_EVENT_EXT, &encode);
        if (ret != PFM_SUCCESS) {
            fprintf(stderr, "Failed to get encoding for event %d: %s\n",
                    i, pfm_strerror(ret));
            return EXIT_FAILURE;
        }

        int new_fd = perf_event_open(encode.attr, -1, i, -1, 0);
        if (new_fd == -1) {
            fprintf(stderr, "Error opening event[%s] config=0x%llx\n",
                    names[i], pe.config);
            return EXIT_FAILURE;
        }
        fd_arr.push_back(new_fd);
    }

    // -----------------------------------------------------------------------
    // 4. Scan: probe every STRIDE bytes and record (va, pa, slice)
    //
    //    Results are written to outputs/slice_mapping.csv.
    // -----------------------------------------------------------------------
    const uint64_t n_probes = BUF_SIZE / STRIDE;
    fprintf(stderr, "Probing %zu addresses (stride=%zu B, %d reps each)...\n",
            n_probes, STRIDE, N_REPS);

    FILE *output_fp = fopen("outputs/slice_mapping.csv", "w");
    fprintf(output_fp, "va,pa,slice\n");

    for (uint64_t idx = 0; idx < n_probes; idx++) {
        uint64_t *target = (uint64_t *)((char *)Array + idx * STRIDE);

        int slice = probe_slice(target);

        void *va = (void *)target;
        unsigned long long pme = get_pagemap_entry(va);
        unsigned long long pfn = pme & ((1ULL << 55) - 1);
        unsigned long long pa  = (pfn << 12) | ((unsigned long long)va & 0xFFF);

        fprintf(output_fp, "%p,0x%012llx,%d\n", va, pa, slice);

        // Progress report every 1000 probes
        if ((idx + 1) % 1000 == 0)
            fprintf(stderr, "\r%zu / %zu (%.2f%%)", idx + 1, n_probes, ((double)(idx + 1) / n_probes)*100);
    }

    fclose(output_fp);
    // -----------------------------------------------------------------------
    // 5. Cleanup
    // -----------------------------------------------------------------------
    munmap(Array, BUF_SIZE);
    return 0;
}