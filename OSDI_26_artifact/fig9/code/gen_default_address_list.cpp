// Generate a list of physical addresses (one per cache line) for an anonymous
// memory region of a given working-set size.
//
// Output file:
//   data/address_list-default/address_list.<workingset_size_mb>.csv
//
// Notes:
// - This uses /proc/self/pagemap to translate a virtual address to a physical
//   address. On many Linux kernels, reading pagemap is restricted and may
//   require root privileges or CAP_SYS_ADMIN.
// - The program touches each cache line before translation to make sure the
//   page is faulted in.

#include <stdint.h>
#include <stdlib.h>
#include <unistd.h> // for close()
#include <random>
#include <cstring>
#include <algorithm>
#include <sys/mman.h>
#include <csignal>
#include <iostream>
#include <fstream>
#include <fcntl.h>
#include <cstdint>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>

// Size of a /proc/*/pagemap entry (64-bit).
const size_t PAGEMAP_ENTRY_SIZE = 8;
// Bitmask for extracting PFN (Page Frame Number): bits [0:54].
const uint64_t PFN_MASK = 0x7FFFFFFFFFFFFF;
// Bit indicating whether the page is present (bit 63).
const uint64_t PAGE_PRESENT = 1ULL << 63;
const size_t PAGE_SIZE = 4096;

uint64_t *array;

uintptr_t get_physical_address(uintptr_t virtual_addr);
int init_array(uint64_t *array, int entry_count);

int main(int argc, char **argv)
{
    // Working-set size in MiB.
    int workingset_size_mb = atoi(argv[1]);

    // Allocate an anonymous region (private) of the requested size.
    array = (uint64_t*)mmap(NULL, workingset_size_mb<<20, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);

    if (!array) return -1;
    int start_idx0 = init_array(array, workingset_size_mb);

    char log_name[1024];
    char pwd[512];
    if (getcwd(pwd, sizeof(pwd)) == NULL) {
        printf("failed pwd\n");
        return -1;
    }
    snprintf(log_name, sizeof(log_name), "%s/data/address_list-default/address_list.%d.csv", pwd, workingset_size_mb);
    int log_fd = open(log_name, O_RDWR | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR);

    // Number of 64B cache lines in the region.
    size_t total_lines = (workingset_size_mb << 20) / 64;
    for(int i=0; i<total_lines; i++)
    {   
        // Touch one 8B word per cache line to make sure the page is resident.
        array[i<<3] = 0;
        uintptr_t vaddr = (uintptr_t)&array[i << 3];
        uintptr_t paddr = get_physical_address(vaddr);
        if (paddr == 0) {
            std::cerr << "Failed to get physical address for virtual address: " << std::hex << vaddr << std::dec << std::endl;
            continue;
        }
        dprintf(log_fd, "0x%lx\n", paddr);
    }
    
    close(log_fd);
    return 0;
}

int init_array(uint64_t *array, int entry_count) {
    std::vector<int> index_arr;
    for(int i=0; i<entry_count; i++) {
        int start_page_idx = i * 64; // 64 cache lines per page
        for(int k=0; k<64; k++) {
            index_arr.push_back(start_page_idx + k);
        }
    }

    std::random_device rd;  // a seed source for the random number engine
    std::shuffle(index_arr.begin(), index_arr.end(), std::mt19937(rd()));

    int total_entries = index_arr.size();
    for(long long s=0; s<total_entries-1; s++) {
		array[(index_arr[s]<<3)] = (uint64_t)&array[(index_arr[s+1]<<3)];
	}
    array[(index_arr[total_entries-1])<<3] = (uint64_t)&array[(index_arr[0]<<3)];

    return index_arr[0];
}

// Convert a virtual address to a physical address using /proc/self/pagemap.
uintptr_t get_physical_address(uintptr_t virtual_addr) {
    // 1) Open the pagemap file.
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0) {
        perror("open /proc/self/pagemap failed (Are you root?)");
        return 0;
    }

    // 2) Compute the virtual page number (VPN).
    unsigned long vpn = virtual_addr / PAGE_SIZE;

    // 3) Compute file offset (VPN * 8 bytes).
    off_t offset = vpn * PAGEMAP_ENTRY_SIZE;

    // 4) Seek to the entry.
    if (lseek(fd, offset, SEEK_SET) == -1) {
        perror("lseek failed");
        close(fd);
        return 0;
    }

    // 5) Read the 64-bit entry.
    uint64_t entry;
    if (read(fd, &entry, PAGEMAP_ENTRY_SIZE) != PAGEMAP_ENTRY_SIZE) {
        perror("read failed");
        close(fd);
        return 0;
    }

    close(fd);

    // 6) Check whether the page is present in physical memory (not swapped out).
    if ((entry & PAGE_PRESENT) == 0) {
        std::cerr << "Page is not present in physical memory (swapped out or unallocated)." << std::endl;
        return 0;
    }

    // 7) Extract PFN and compose the physical address.
    unsigned long pfn = entry & PFN_MASK;
    uintptr_t physical_addr = (pfn * PAGE_SIZE) + (virtual_addr % PAGE_SIZE);

    return physical_addr;
}