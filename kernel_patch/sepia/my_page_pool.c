#include <linux/my_page_pool.h>
#include <net/page_pool/types.h>
#include <linux/sysctl.h> 
#include <linux/init.h>
#include <linux/mm.h> 
#include <linux/gfp.h> 
#include <linux/dma-mapping.h> 
#include <linux/slab.h> 
#include <linux/export.h>


struct my_allocated_page_list* my_page_list = NULL;


int sysctl_test_create_flag_numa0 = 0;

EXPORT_SYMBOL_GPL(sysctl_test_create_flag_numa0);


void sepia_init(struct device* dev, int numa_id)
{

	printk("sepia_init : numa_id(%d)\n", numa_id);
    int i, j;
    void *dma_memory;
	dma_addr_t dma_handle;

	// create the main structure to manage the pages
	if(!my_page_list)
	{
		my_page_list = kzalloc(sizeof(struct my_allocated_page_list), GFP_KERNEL);
		for(i=0; i<CPU_NUM_TOTAL; i++)
			my_page_list->prev_group_per_cpu[i] = 0;

		for(i=0; i<CPU_NUM_TOTAL; i++)
			for(j=0; j<PAGE_GROUP; j++)
				my_page_list->page_idx[i][j] = -1;
	}

	if(!my_page_list->page_sequence)
	{
		my_page_list->page_sequence = kzalloc(CPU_NUM_TOTAL * sizeof(struct page ***), GFP_KERNEL);
		for (i = 0; i < CPU_NUM_TOTAL; i++)
			my_page_list->page_sequence[i] = kzalloc(PAGE_GROUP * sizeof(struct page **), GFP_KERNEL);
		for (i = 0; i < CPU_NUM_TOTAL; i++)
			for (j = 0; j < PAGE_GROUP; j++)
				my_page_list->page_sequence[i][j] = kzalloc(PAGES_PER_GROUP * sizeof(struct page *), GFP_KERNEL);
	}

	if(!my_page_list->avail_mask)
	{
		my_page_list->avail_mask = kzalloc(CPU_NUM_TOTAL * sizeof(uint64_t **), GFP_KERNEL);
		for (i = 0; i < CPU_NUM_TOTAL; i++)
			my_page_list->avail_mask[i] = kzalloc(PAGE_GROUP * sizeof(uint64_t *), GFP_KERNEL);
		for (i = 0; i < CPU_NUM_TOTAL; i++)
			for (j = 0; j < PAGE_GROUP; j++)
				my_page_list->avail_mask[i][j] = kzalloc(MASKS_PER_GROUP * sizeof(uint64_t), GFP_KERNEL);
		
		// initialize all bits to 1 for each CPU
		for(i=0; i<CPU_NUM_TOTAL; i++)
			for(j=0; j<PAGE_GROUP; j++)
				for(int k=0; k<MASKS_PER_GROUP; k++)
					my_page_list->avail_mask[i][j][k] = ~0ULL;

		for(i=0; i<CPU_NUM_TOTAL; i++)
		{
			for(j=0; j<PAGE_GROUP; j++)
			{
				int valid_bits = PAGES_PER_GROUP - (MASKS_PER_GROUP - 1) * BITS_PER_MASK;
				if (valid_bits < BITS_PER_MASK) {
					uint64_t mask = (1ULL << valid_bits) - 1;
					my_page_list->avail_mask[i][j][MASKS_PER_GROUP - 1] &= mask;
				}
			}
		}
	}

	size_t total_size = PAGE_GROUP * PAGES_PER_GROUP * PAGE_SIZE * CPU_NUM_PER_NUMA;

	dma_memory = dma_alloc_coherent(dev, total_size, &dma_handle, GFP_KERNEL);

	if (!dma_memory){
		printk(KERN_ERR "NUMA %d: DMA memory allocation failed\n", numa_id);
		return;
	}
	printk("NUMA %d: dma_memory(%llx), dma_memory_phys(%llx), dma_handle(%llx)\n", numa_id, (unsigned long long)dma_memory, (unsigned long long)virt_to_phys(dma_memory), dma_handle);

	void *base_vaddr = dma_memory;   
	dma_addr_t base_dma = dma_handle;
	
	// adjust the target physical address to start from 0x101500000
	phys_addr_t target_phys_addr = 0x101500000ULL;
	phys_addr_t current_phys_addr = virt_to_phys(base_vaddr);
	
	if (current_phys_addr < target_phys_addr) {
		size_t offset = target_phys_addr - current_phys_addr;
		base_vaddr += offset;
		base_dma += offset;
		printk("NUMA %d: Adjusted base addresses - offset: 0x%lx, new phys addr: 0x%llx\n", 
			   numa_id, offset, (unsigned long long)virt_to_phys(base_vaddr));
	}
	
	my_page_list->memory_start = virt_to_phys(base_vaddr);
	my_page_list->memory_end = virt_to_phys(base_vaddr + total_size);


	size_t global_idx = 0;
	
	if(numa_id==0)
	{
		printk("numa_id(%d) sepia_init for NUMA 0 start\n", numa_id);
		for(int cpu=0; cpu<CPU_NUM_TOTAL; cpu+=2) // CPU 0, 2, 4, 6, ...
		{
			for (i = 0; i < PAGES_PER_GROUP; i++) {
				for (j = 0; j < PAGE_GROUP; j++) {
					void *vaddr = base_vaddr + global_idx * PAGE_SIZE;
					struct page *pg = virt_to_page(vaddr);
					
					dma_addr_t dmaaddr = base_dma + global_idx * PAGE_SIZE;
					
					pg->dma_addr = dmaaddr;
		
					my_page_list->page_sequence[cpu][j][i] = pg;
					
					global_idx++;
				}
			}
		}
	}
	
	return;
}
EXPORT_SYMBOL_GPL(sepia_init);



int check_page_number(struct page *page)
{
	unsigned long phys;
	
	if (!my_page_list || !page)
		return -1;
		
	phys = page_to_phys(page);
	
	if (phys >= my_page_list->memory_start && phys <= my_page_list->memory_end)
		return 1;
	
	return -1; 
}
EXPORT_SYMBOL_GPL(check_page_number);




struct page* sepia_alloc(int cpu_num)
{
    int i, cur_group;
    int mask, bit, page_idx;
    int start_group = my_page_list->prev_group_per_cpu[cpu_num];
    for (i = 0; i < PAGE_GROUP; i++) {
        cur_group = (start_group + i) % PAGE_GROUP;
        for (mask = 0; mask < MASKS_PER_GROUP; mask++) {
            uint64_t word = my_page_list->avail_mask[cpu_num][cur_group][mask];

            if (word != 0) {  
                bit = __ffs(word);
                page_idx = mask * BITS_PER_MASK + bit;
        
                struct page *allocated_page = my_page_list->page_sequence[cpu_num][cur_group][page_idx];
                my_page_list->avail_mask[cpu_num][cur_group][mask] = word & ~(1ULL << bit);
                my_page_list->prev_group_per_cpu[cpu_num] = (cur_group + 1) % PAGE_GROUP;

                return allocated_page;
            }
        }
    }
    return NULL;
//------------------------------------------------------------------------------------------
}
EXPORT_SYMBOL_GPL(sepia_alloc);


void make_page_available(struct page *page)
{
// NUMA 0 only - optimized version
	unsigned long phys;
	size_t page_offset, cpu_num, page_in_cpu;
	int group, page_idx;
	int word, bit;
	
	const size_t pages_per_cpu = PAGE_GROUP * PAGES_PER_GROUP;
	
	phys = page_to_phys(page);
	
	page_offset = (phys - my_page_list->memory_start) >> PAGE_SHIFT;
	
	cpu_num = (page_offset / pages_per_cpu) * 2;
	page_in_cpu = page_offset % pages_per_cpu;
	
	group = page_in_cpu % PAGE_GROUP;
	page_idx = page_in_cpu / PAGE_GROUP;
	
	word = page_idx / BITS_PER_MASK;
	bit = page_idx % BITS_PER_MASK;
	
	my_page_list->avail_mask[cpu_num][group][word] |= (1ULL << bit);
}
EXPORT_SYMBOL_GPL(make_page_available);



static struct ctl_table my_sysctl_table[] = {
	{
        .procname       = "test_create_flag_numa0",
        .data           = &sysctl_test_create_flag_numa0,
        .maxlen         = sizeof(unsigned int),
        .mode           = 0644,
        .proc_handler   = &proc_douintvec,
    },
    {}
};

static struct ctl_table_header *my_page_pool_sysctl_header;

static int __init my_page_pool_init(void)
{
    my_page_pool_sysctl_header = register_sysctl("my_page_pool", my_sysctl_table);
    if (!my_page_pool_sysctl_header) {
        printk(KERN_ERR "my_page_pool: Failed to register sysctl table\n");
        return -ENOMEM;
    }
    return 0;
}


static void __exit my_page_pool_exit(void)
{
    if (my_page_pool_sysctl_header) {
        unregister_sysctl_table(my_page_pool_sysctl_header);
    }
}

core_initcall(my_page_pool_init);