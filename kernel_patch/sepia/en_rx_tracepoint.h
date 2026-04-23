#undef TRACE_SYSTEM
#define TRACE_SYSTEM mlx5_rx

#if !defined(_MLX5_EN_RX_TP_) || defined(TRACE_HEADER_MULTI_READ)
#define _MLX5_EN_RX_TP_

#include <linux/tracepoint.h>

TRACE_EVENT(mlx5_mpwqe_page_alloc,

	TP_PROTO(int cpu, u16 wqe_idx, int page_idx, u64 phys_addr),

	TP_ARGS(cpu, wqe_idx, page_idx, phys_addr),

	TP_STRUCT__entry(
		__field(int, cpu)
		__field(u16, wqe_idx)
		__field(int, page_idx)
		__field(u64, phys_addr)
	),

	TP_fast_assign(
		__entry->cpu = cpu;
		__entry->wqe_idx = wqe_idx;
		__entry->page_idx = page_idx;
		__entry->phys_addr = phys_addr;
	),

	TP_printk("cpu=%d wqe_idx=%u page_idx=%d phys_addr=0x%llx",
		  __entry->cpu, __entry->wqe_idx, 
		  __entry->page_idx, __entry->phys_addr)
);

#endif /* _MLX5_EN_RX_TP_ */

#undef TRACE_INCLUDE_PATH
#define TRACE_INCLUDE_PATH diag
#undef TRACE_INCLUDE_FILE
#define TRACE_INCLUDE_FILE en_rx_tracepoint
#include <trace/define_trace.h>

