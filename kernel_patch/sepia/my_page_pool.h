#ifndef MY_PAGE_POOL_H
#define MY_PAGE_POOL_H

#include <linux/types.h>
#include <linux/mm_types.h>


#define PAGE_GROUP 32
#define PAGES_PER_GROUP 128 // 4KB * 128 = 0.5MB ,4KB * 256 = 1MB
#define CPU_NUM_TOTAL 36
#define CPU_NUM_PER_NUMA 18

#define BITS_PER_MASK 64
#define MASKS_PER_GROUP ((PAGES_PER_GROUP + BITS_PER_MASK - 1) / BITS_PER_MASK) 

struct my_allocated_page_list {
    struct page ****page_sequence; // CPU-wise page management: [CPU][GROUP][PAGES_PER_GROUP]
    
    phys_addr_t memory_start;
    phys_addr_t memory_end;

    int prev_group_per_cpu[CPU_NUM_TOTAL];
    int page_idx[CPU_NUM_TOTAL][PAGE_GROUP];

    uint64_t ***avail_mask;
};

struct page *sepia_alloc(int);
int check_page_number(struct page *);
void make_page_available(struct page *);
#endif /* MY_PAGE_POOL_H */