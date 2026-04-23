#!/bin/bash

# ==========================================
# SPDK Experiment Configuration
# ==========================================

# Target connection information
TR_ADDR="192.168.10.211"
TR_SVCID="4420"
SUB_NQN="nqn.2020-07.com.midhul:null0" 

# Transport ID
TRID="trtype:TCP adrfam:IPv4 traddr:${TR_ADDR} trsvcid:${TR_SVCID} subnqn:${SUB_NQN}"

# number of trials
TRIALS=1

test_duration=30
output_dir="./spdk_results_$(date +%Y%m%d_%H%M%S)"

# === experiment parameters ===
block_sizes=(65536 131072)
declare -A qd_for_bs
qd_for_bs[65536]="16"
qd_for_bs[131072]="16"

flow_configs=(2 4 6 8 16)

rw_mode="randread"

# ==========================================

mkdir -p ${output_dir}
echo "Results will be saved to: ${output_dir}"

function cleanup() {
    sudo killall perf > /dev/null 2>&1
}
trap cleanup EXIT

cleanup_after_test() {
    sudo killall -q -9 perf 2>/dev/null || true
    sync
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    sleep 1
}

# 2. Main Experiment Loops
for bs in "${block_sizes[@]}"; do
    echo ""
    echo "========================================"
    echo "=== BLOCK SIZE: ${bs} Bytes ==="
    
    read -ra queue_depths <<< "${qd_for_bs[$bs]}"

    for qd in "${queue_depths[@]}"; do
        for flows in "${flow_configs[@]}"; do
            
            echo "  [Progress] BS=${bs}, QD=${qd}, Flows=${flows} (Running ${TRIALS} Trials)..."

            for ((t=1; t<=TRIALS; t++)); do
                
                prefix="${bs}B_qd${qd}_flows${flows}_trial${t}"
                
                pids=()
                
                for ((i=0; i<flows; i++)); do
                    core_id=$((i * 2))
                    let "mask_dec = 1 << core_id"
                    core_mask=$(printf "0x%x" $mask_dec)
                    
                    if [ -z "$core_list_sar" ]; then core_list_sar="${core_id}"; else core_list_sar="${core_list_sar},${core_id}"; fi

                    spdk/build/examples/perf \
                        -c ${core_mask} -r "${TRID}" -q ${qd} -o ${bs} \
                        -w ${rw_mode} -t ${test_duration} -L \
                        > "${output_dir}/perf_${prefix}_flow${i}.txt" 2>&1 &
                    
                    pids+=($!)
                    sleep 0.2
                done

                for pid in "${pids[@]}"; do wait $pid; done
                echo -n "."

                cleanup_after_test
                sleep 2
                
            done

            echo " Done."

        done
    done
done

echo ""
echo "Experiment Completed! All logs are in ${output_dir}"