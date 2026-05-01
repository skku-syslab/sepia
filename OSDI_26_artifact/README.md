# USENIX OSDI 2026 Artifact Evaluation

## 1. Hardware Configurations
Our hardware configurations used in the paper are:
- CPU: 2-socket Intel Xeon Gold 6354 3.0GHz with 18 cores per socket.
- Tested Architectures: Intel Ice Lake (e.g., Xeon 6354)
- LLC Specs: 39MB LLC, 12-way associativity, 2048 sets, and 26 slices.
- RAM: 256GB DRAM
- NIC: NVIDIA ConnectX-6 (200Gbps).
- Network Setup: Two physical machines directly connected via a 200Gbps link.


[**Caveats of our work**]
- **LLC Architectural Dependency**: Sepia's color-aware page allocation relies on specific LLC microarchitectural details, such as the width of the set-index field and the slice-hash function. The current methodology was tested on Intel Ice Lake and Emerald Rapids processors; future models with different set-index widths may require updates to the page-grouping logic.
- **Performance Requirements**: To reproduce the 200Gbps link saturation with high CPU efficiency (as shown in Figure 13), the target hardware must support 200Gbps line rates and Intel DDIO.
- **System Prerequisites**: The following system settings must be applied to match our experimental environment:
    - Disable: Hyper-threading, IOMMU, and irqbalance.
    - Enable: Jumbo Frames (9000B MTU), TCP Segmentation Offload (TSO), and Generic Receive Offload (GRO).
- **NUMA and Core Mapping**: Our evaluation mainly utilizes cores sharing the same LLC to measure contention.


## 2. Experiments (with root)

**For more stable and reproducible results, we recommend rebooting both machines between figures.**

**(Don't forget to be root)**

### Figure 3.

- Kernel: both machines boot with `6.6.41-default`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)
- Run (on server):
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig3/default
    ./enable_arfs_2.sh
    ./run_all_tests.sh
    python3 extract_data.py

    cd /usr/src/sepia/OSDI_26_artifact/fig3/throttle
    ./run_all_tests.sh
    python3 extract_data.py
    ```

### Figure 4.

- Kernel: both machines boot with `6.6.41-default`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)
- run Figure 4(a) (server-side)
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig4/a
    ./enable_arfs_2.sh
    ./default_one_flow.sh
    python3 extract_data.py
    ```
    - check: LLC miss rate

- run Figure 4(b),(c)
    - set descriptor 2048 on 192.168.10.211
    ```bash
    ethtool -G ens2np0 rx 2048 tx 2048
    ```
    - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig4/b_c
    ./enable_arfs_2.sh
    ./run_all_tests.sh
    python3 extract_data.py
    ```
    - check: packet-occupied and LLC miss rate


### Figure 5. (Help Needed)

- Kernel: both machines boot with `6.6.41-default`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- patch kernel on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig5
  cp kernel_patch_code/en_rx.c /usr/src/linux-6.6.41-default/drivers/net/ethernet/mellanox/mlx5/core/

  cd /usr/src/linux-6.6.41-default
  make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
  ```

- run Figure 5(a),(b) on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig5
  ./scripts/0_run_all.sh
  ```
  - check: `plots/subfig_a.png` and `plots/subfig_b.png`

- restore kernel patch on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/kernel_patch/default
  cp en_rx.c /usr/src/linux-6.6.41-default/drivers/net/ethernet/mellanox/mlx5/core/

  cd /usr/src/linux-6.6.41-default
  make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
  ```

### Figure 9.

- This is a simulation-based experiment and is machine- and kernel-agnostic.
- Since running the full Tetris algorithm is time-consuming, a pre-generated dataset is provided under `dummy_data/` and is used by default.

- run:
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig9
  bash scripts/0_run_all.sh
  ```
  - check: `plots/figure.png`


### Figure 10.

- This is a simulation-based experiment and is machine- and kernel-agnostic.
- Figure 10 reuses the Tetris block layout computed in Figure 9; the same `dummy_data/`-based mocking applies here as well.

- run:
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig10
  bash scripts/0_run_all.sh
  ```
  - check: `plots/subfigure_a.png` and `plots/subfigure_b.png`
  - note: the violation ratio reported in the paper may differ slightly in practice, as it is sensitive to the chosen address range and the probabilistic nature of the Tetris layout process.


### Figure 13.

- Kernel: both machines boot with `6.6.41-sepia`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- pre-setup on 192.168.10.211
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig13
  ./sepia_with_no_aRFS.sh
  ```

- run Figure 13(a),(b) on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig13/sepia/iperf_sar/
  ./sepia_init.sh
  ./run_all_tests.sh
  python3 extract_data.py
  ```

- run Figure 13(c) on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig13/sepia/iperf_sar_missrate/
  ./run_all_tests.sh
  python3 extract_data.py
  ```
  - check: throughput-per-core, total throughput, utilization, LLC miss rate



### Figure 14.

- Kernel: both machines boot with `6.6.41-sepia`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- pre-setup on 192.168.10.211
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig14
  ./sepia_with_no_aRFS.sh
  ```

- run on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig14
  ./sepia_init.sh
  ./run_all_tests.sh
  python3 extract_data.py
  ```
  - check: working set size = packet-occupied + (4MB * number of flows)



### Figure 15.

- Run both default and sepia experiments; run default first.
- Kernel (default phase): both machines boot with `6.6.41-default`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- run default phase on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig15/iperf_sar/default
  ./enable_arfs_2.sh
  ./run_all_tests.sh 10
  python3 extract_data.py
  python3 extract_data.py --aggregate .
  cat flow_averages.csv

  cd /usr/src/sepia/OSDI_26_artifact/fig15/iperf_sar_missrate/default
  ./run_all_tests.sh 10
  python3 extract_data.py
  python3 extract_data.py --aggregate .
  cat flow_averages.csv
  ```
  - check: throughput-per-core, total throughput, LLC miss rate
  - note: adjust repetition count with `./run_all_tests.sh N`


- Kernel (sepia phase): both machines boot with `6.6.41-sepia`

- pre-setup on 192.168.10.211
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig15/
  ./sepia_with_no_aRFS.sh
  ```

- run sepia phase on 192.168.10.213
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig15/iperf_sar/sepia
  ./sepia_init.sh
  ./run_all_tests.sh 10
  python3 extract_data.py
  python3 extract_data.py --aggregate .
  cat flow_averages.csv

  cd /usr/src/sepia/OSDI_26_artifact/fig15/iperf_sar_missrate/sepia
  ./run_all_tests.sh 10
  python3 extract_data.py
  python3 extract_data.py --aggregate .
  cat flow_averages.csv
  ```
  - check: throughput-per-core, total throughput, LLC miss rate
  - note: adjust repetition count with `./run_all_tests.sh N`


### Figure 16.

- Use Figure 3 and Figure 13 results for Default and Sepia baselines.
- Run only `Default + Ring Throttling` and `Default + Stride-1`.
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- run `Default + Ring Throttling`
  - kernel: both machines boot with `6.6.41-default`
  - pre-setup on 192.168.10.211
    ```bash
    ethtool -G ens2np0 rx 256 tx 256
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig16/Default_Ring_Thrtt
    ./enable_arfs_2.sh
    ./run_all_tests.sh
    python3 extract_data.py
    ```
  - check: throughput-per-core

- run `Default + Stride-1`
  - kernel: patch and boot `6.6.41-sepia`
  - apply patch
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig16/Default_Stride
    cp sepia_page_pool.h /usr/src/linux-6.6.41-sepia/include/linux/
    cd /usr/src/linux-6.6.41-sepia
    make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
    ```
  - pre-setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig16/Default_Stride
    ./Default_Stride_setting.sh
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig16/Default_Stride
    ./sepia_init.sh
    ./run_all_tests.sh
    python3 extract_data.py
    ```
  - check: throughput-per-core

- restore sepia kernel patch
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/kernel_patch/sepia
  cp sepia_page_pool.h /usr/src/linux-6.6.41-sepia/include/linux/
  cd /usr/src/linux-6.6.41-sepia
  make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
  ```

### Table 1.

- Run four modes: `Default`, `Default w/Ring-Thrtt`, `Default w/Stride-1`, `Sepia`
- Roles: `192.168.10.213` (server), `192.168.10.211` (client)

- run `Default`
  - kernel: both machines boot with `6.6.41-default`
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Default
    ./enable_arfs_2.sh
    ./four_flow_test.sh
    cat four_flow_1/imc_read_test.log
    ```
  - check: `total_bw`

- run `Default w/Ring-Thrtt`
  - kernel: both machines boot with `6.6.41-default`
  - pre-setup on 192.168.10.211
    ```bash
    ethtool -G ens2np0 rx 256 tx 256
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Default_Ring_Thrtt
    ./enable_arfs_2.sh
    ./four_flow_test.sh
    cat four_flow_1/imc_read_test.log
    ```
  - check: `total_bw`

- run `Default w/Stride-1`
  - kernel: patch and boot `6.6.41-sepia`
  - apply patch
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Default_Stride
    cp sepia_page_pool.h /usr/src/linux-6.6.41-sepia/include/linux/
    cd /usr/src/linux-6.6.41-sepia
    make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
    ```
  - pre-setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Default_Stride
    ./Default_Stride_setting.sh
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Default_Stride
    ./sepia_init.sh
    ./four_flow_test.sh
    cat four_flow_1/imc_read_test.log
    ```
  - check: `total_bw`

- restore sepia kernel patch
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/kernel_patch/sepia
  cp sepia_page_pool.h /usr/src/linux-6.6.41-sepia/include/linux/
  cd /usr/src/linux-6.6.41-sepia
  make -j$(nproc) bzImage && make -j$(nproc) modules && make INSTALL_MOD_STRIP=1 modules_install && make install
  ```

- run `Sepia`
  - kernel: both machines boot with `6.6.41-sepia`
  - pre-setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Sepia
    ./sepia_with_no_aRFS.sh
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/table1/Sepia
    ./sepia_init.sh
    ./four_flow_test.sh
    cat four_flow_1/imc_read_test.log
    ```
  - check: `total_bw`



### Figure 17.

- Roles: `192.168.10.211` (target), `192.168.10.213` (host)
- This experiment uses shared `common/spdk` for both `default` and `sepia`.
- rebuild SPDK before running experiments.

- prepare SPDK link and build (once)
  ```bash
  cd /usr/src/sepia/OSDI_26_artifact/fig17
  ln -sfn ../common/spdk default/spdk
  ln -sfn ../common/spdk sepia/spdk

  cd /usr/src/sepia/OSDI_26_artifact/fig17/default
  sudo ./spdk/scripts/pkgdep.sh
  make -C ./spdk clean
  ./spdk/configure
  make -C ./spdk -j$(nproc)
  ```

- run `default` phase
  - kernel: both machines boot with `6.6.41-default`
  - target setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig17/default
    cp target_config.sh config.sh
    ./prepare_env.sh
    ./run_target.sh 0xFFFFFFFFF
    ```
  - host run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig17/default
    cp host_config.sh config.sh
    ./prepare_env.sh
    ./my_spdk_test.sh
    ./parse_results.sh spdk_results_xxxxxxxx_xxxxxx/
    cat spdk_results_xxxxxxxx_xxxxxx/summary_avg.csv
    ```
  - check: `AvgThroughput(MiB/s)`

- run `sepia` phase
  - kernel: both machines boot with `6.6.41-sepia`
  - target setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig17/sepia
    cp target_config.sh config.sh
    ./sepia_with_no_aRFS.sh
    ./prepare_env.sh
    ./run_target.sh 0xFFFFFFFFF
    ```
  - host run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig17/sepia
    cp host_config.sh config.sh
    ./sepia_init.sh
    ./prepare_env.sh
    ./my_spdk_test.sh
    ./parse_results.sh spdk_results_xxxxxxxx_xxxxxx/
    cat spdk_results_xxxxxxxx_xxxxxx/summary_avg.csv
    ```
  - check: `AvgThroughput(MiB/s)`





### Figure 18.

- Roles: `192.168.10.211` (server, nginx), `192.168.10.213` (client, wrk)
- Workload: POST requests with 2MB/4MB payloads from `wrk` to `nginx`

- install dependencies
  - on 192.168.10.211
    ```bash
    sudo apt update
    sudo apt install -y nginx
    ```
  - on 192.168.10.213
    ```bash
    sudo apt update
    sudo apt install -y wrk
    ```

- configure nginx on 192.168.10.211 (required)
  - edit `/etc/nginx/sites-available/default`
    - in the `server { ... }` block, add:
      - `client_max_body_size 0;`
    - in `location / { ... }`, add:
      - `error_page 405 =200 $uri;`
  - minimal example:
    ```nginx
    server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;
        server_name _;
        client_max_body_size 0;

        location / {
            try_files $uri $uri/ =404;
            error_page 405 =200 $uri;
        }
    }
    ```
  - edit `/etc/nginx/nginx.conf`
    - set:
      - `worker_processes 18;`
      - `worker_cpu_affinity auto 10101010101010101010101010101010101;`
  - apply and validate
    ```bash
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl status nginx --no-pager
    ps -eo pid,psr,comm | grep nginx
    ```

- run `default` phase
  - kernel: both machines boot with `6.6.41-default`
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig18/default
    ./run_nginx_POST.sh
    python3 parse_results_POST.py nginx_result_xxxxxxxx_xxxxxx/
    ```
  - check: `Avg Gbps`

- run `sepia` phase
  - kernel: both machines boot with `6.6.41-sepia`
  - pre-setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig18/sepia
    ./sepia_with_no_aRFS.sh
    ```
  - run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig18/sepia
    ./sepia_with_no_aRFS.sh
    ./run_nginx_POST.sh
    python3 parse_results_POST.py nginx_result_xxxxxxxx_xxxxxx/
    ```
  - check: `Avg Gbps`



### Figure 19.

- Roles: `192.168.10.211` (server, memcached), `192.168.10.213` (client, memtier)
- Workload: memtier sends SET requests to memcached

- install dependencies
  - on 192.168.10.211 (server)
    ```bash
    sudo apt update
    sudo apt install -y memcached
    ```
  - on 192.168.10.213 (client)
    ```bash
    sudo apt update
    sudo apt install -y memtier-benchmark
    ```
  - verify
    ```bash
    memcached -h | head -n 1
    memtier_benchmark --version
    ```

- run `default` phase
  - kernel: both machines boot with `6.6.41-default`
  - server setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig19/default
    ./enable_arfs_2.sh
    ./running_memcached.sh
    ```
  - client run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig19/default
    ./memcached_100_set.sh
    ./parse_memcached.sh memcached_set_results_xxxxxxxx_xxxxxx/
    cat memcached_set_results_xxxxxxxx_xxxxxx/summary_memcached.csv
    ```
  - check: `AvgBandwidth(KB/s)`

- run `sepia` phase
  - kernel: both machines boot with `6.6.41-sepia`
  - server setup on 192.168.10.211
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig19/sepia
    ./sepia_server.sh
    ./running_memcached.sh
    ```
  - client setup and run on 192.168.10.213
    ```bash
    cd /usr/src/sepia/OSDI_26_artifact/fig19/sepia
    ./sepia_client.sh
    ./memcached_100_set.sh
    ./parse_memcached.sh memcached_set_results_xxxxxxxx_xxxxxx/
    cat memcached_set_results_xxxxxxxx_xxxxxx/summary_memcached.csv
    ```
  - check: `AvgBandwidth(KB/s)`
