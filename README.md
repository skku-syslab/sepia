# When DDIO Meets Page Coloring: Revisiting DDIO Performance with Sepia

**Sepia** is a novel color-aware page allocator for CPU-efficient network I/O processing. The performance of Intel's Data Direct I/O (DDIO) is often constrained by the "leaky DMA" problem, where packet data is evicted from the last-level cache (LLC) before processing completes. Our analysis reveals that conflict misses, rather than capacity limitations alone, are the primary cause of these LLC misses. 

**Sepia** minimizes LLC misses by leveraging a deeper understanding of sliced LLC architecture through its **Sepia** Manager, which constructs per-core colored page pools, and the **Sepia** Allocator, which employs a low-conflict, stride-1 allocation pattern.

While maintaining low LLC miss rates, **Sepia** achieves up to 1.51× higher throughput and saturates a 200Gbps link using 2.5 fewer CPU cores than the default Linux network stack.


## Repository Overview

This repository includes the Sepia implementation for the Linux kernel and the reproduction scripts for the OSDI'26 Artifact Evaluation:

- `kernel_patch/`: Contains the Sepia core implementation (Sepia Manager and Sepia Allocator) and the baseline configuration for Linux kernel 6.6.41.
- `OSDI_26_artifact/`: Includes automated scripts for reproducing the evaluation results presented in the OSDI'26 paper, including microbenchmarks and real-world applications.
- `arch_scripts/`: Includes automated scripts for determining system-dependent parameter values (e.g., \#page groups). 


## Getting Started Guide

Sepia has been successfully tested on systems equipped with Intel Ice Lake or Emerald Rapids processors and NVIDIA ConnectX-6 NICs, running Ubuntu 20.04 with Linux kernel 6.6.41. Our evaluation requires two physical machines, a client and a server. You must perform the kernel installation steps on both machines to ensure the entire testbed is consistent.

This guide consists of three parts:

1. **Build and install the default kernel (baseline) and the Sepia kernel**

2. Configure passwordless SSH between two machines

3. Run toy experiments


## 1. Build and Install Kernels (on BOTH Machines) (with root)

We recommend placing the kernel sources in `/usr/src` to maintain a consistent environment.


**(Don't forget to be root)**
### 1. Clone the Repository
```bash
cd /usr/src
git clone https://github.com/skku-syslab/sepia.git
```

### 2. Prepare Kernel Sources
Download and extract the clean Linux 6.6.41 source code:
```bash
cd /usr/src
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.6.41.tar.xz
tar -xf linux-6.6.41.tar.xz
```

### 3. Build and Install the Default Kernel (Baseline)
The default kernel includes minimal patches to trace physical addresses for analysis.
```bash
# Setup source tree
cp -r linux-6.6.41 linux-6.6.41-default
cd sepia/kernel_patch/default

# Apply baseline patches and configuration
cp en_rx.c /usr/src/linux-6.6.41-default/drivers/net/ethernet/mellanox/mlx5/core/
mkdir -p /usr/src/linux-6.6.41-default/drivers/net/ethernet/mellanox/mlx5/core/diag
cp en_rx_tracepoint.h /usr/src/linux-6.6.41-default/drivers/net/ethernet/mellanox/mlx5/core/diag/

# Start from the running kernel config
cp /boot/config-$(uname -r) /usr/src/linux-6.6.41-default/.config

cd /usr/src/linux-6.6.41-default
scripts/config --set-str LOCALVERSION "-default"
scripts/config --set-str SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str SYSTEM_REVOCATION_KEYS ""

# Build and Install
make olddefconfig
make -j$(nproc) bzImage modules
make INSTALL_MOD_STRIP=1 modules_install
make install
```
### 4. Build and Install the Sepia Kernel
The Sepia kernel implements the color-aware page allocator within the `mm/` directory and integrates it with the NIC driver.

#### 4.0 Set `PAGE_GROUP` (system-dependent)

Sepia uses page coloring based on LLC set-index bits that do not overlap with the 4KB page offset. The number of usable colors (page groups) depends on the CPU's LLC configuration, so you may need to update `PAGE_GROUP` before building the Sepia kernel.

- `PAGE_GROUP` is defined in `kernel_patch/sepia/sepia_page_pool.h`.
- Run `arch_scripts/print_llc_configuration.py` on your system and use the printed `Page Groups` value:
   ```bash
   cd /usr/src/sepia
   python3 arch_scripts/print_llc_configuration.py
   ```
   Example:
   ```
   Sets per Slice              : 2048
   Page Groups                 : 32
   ```
   In this case, set `#define PAGE_GROUP 32`.

   Another example (system-dependent):
   ```
   Sets per Slice              : 4096
   Page Groups                 : 64
   ```
   In this case, set `#define PAGE_GROUP 64`.

Note: With 4KB pages and 64B cache lines, `Page Groups = (Sets per Slice) / 64`.

Note: Sepia currently assumes a fixed 16MB page pool per CPU.

If `PAGE_GROUP` changes and you still want to keep the same 16MB pool size, update `PAGES_PER_GROUP` in `kernel_patch/sepia/sepia_page_pool.h` accordingly:
`PAGES_PER_GROUP = (16MB / 4KB) / PAGE_GROUP = 4096 / PAGE_GROUP`.  
Examples:
- `PAGE_GROUP=32` -> `PAGES_PER_GROUP=128`
- `PAGE_GROUP=64` -> `PAGES_PER_GROUP=64`


#### 4.1 Set other system-dependent parameters
- **CPU counts (`kernel_patch/sepia/sepia_page_pool.h`)**
  - `CPU_NUM_TOTAL`: total number of CPUs.
  - `CPU_NUM_PER_NUMA`: number of CPUs used per NUMA node
  - Update these values to match your machine topology before building the Sepia kernel.
  
  - You can check these values with:
      ```bash
      nproc
      lscpu -e=cpu,node | awk 'NR>1 {cnt[$2]++} END {for (n in cnt) print "NUMA node", n ":", cnt[n], "CPUs"}'
      ```
- **NIC interface name**
  - We use `ens2np0` as the default NIC interface name in our setup.
  - If your interface name is different, please update it in:   
   `/usr/src/sepia/kernel_patch/sepia/en_main.c` (`SEPIA_NETDEV_NAME`)  
   `/usr/src/sepia/OSDI_26_artifact/scripts/common_env.sh` (`IFACE`)  
  - The kernel-side Sepia initialization path checks `SEPIA_NETDEV_NAME`, so it must match your NIC interface name. Also, our artifact scripts read `IFACE` from `common_env.sh`, so script-side NIC interface changes are managed in one place.



#### 4.2 Apply Sepia patches and build
After setting `PAGE_GROUP`, apply the Sepia implementation and build/install the kernel as follows.

```bash
# Setup source tree
cd /usr/src
cp -r linux-6.6.41 linux-6.6.41-sepia
cd sepia/kernel_patch/sepia

# Apply Sepia implementation and configuration
cp en_main.c en_rx.c /usr/src/linux-6.6.41-sepia/drivers/net/ethernet/mellanox/mlx5/core/
mkdir -p /usr/src/linux-6.6.41-sepia/drivers/net/ethernet/mellanox/mlx5/core/diag
cp en_rx_tracepoint.h /usr/src/linux-6.6.41-sepia/drivers/net/ethernet/mellanox/mlx5/core/diag/
cp skbuff.h sepia_page_pool.h /usr/src/linux-6.6.41-sepia/include/linux/
cp sepia_page_pool.c Makefile /usr/src/linux-6.6.41-sepia/mm/

# Start from the running kernel config
cp /boot/config-$(uname -r) /usr/src/linux-6.6.41-sepia/.config

cd /usr/src/linux-6.6.41-sepia
scripts/config --set-str LOCALVERSION "-sepia"
scripts/config --set-str SYSTEM_TRUSTED_KEYS ""
scripts/config --set-str SYSTEM_REVOCATION_KEYS ""
scripts/config --enable DMA_NUMA_CMA

# Build and Install
make olddefconfig
make -j$(nproc) bzImage modules
make INSTALL_MOD_STRIP=1 modules_install
make install
```

### 5. Configure Boot Parameters (GRUB) (on BOTH Machines)
Modify /etc/default/grub on both machines to select the target kernel for experiments.
```bash
vi /etc/default/grub
```
- **Option A: Sepia kernel**

Sepia requires CMA reservation to manage colored pages. We reserve 1GB on the DDIO-enabled NUMA node for maximum stability and performance.

Note: In our system, the Sepia page pools use 288MB (16MB × 18 cores) in the DDIO-enabled NUMA **node 0**, so 1GB provides sufficient headroom.

```bash
GRUB_DEFAULT="1>Ubuntu, with Linux 6.6.41-sepia"
GRUB_CMDLINE_LINUX_DEFAULT="numa_cma=0:1G"
```

- **Option B: Default kernel (baseline)**: Standard configuration without CMA reservation.
```bash
GRUB_DEFAULT="1>Ubuntu, with Linux 6.6.41-default"
GRUB_CMDLINE_LINUX_DEFAULT=""
```

- **Apply and Reboot (on BOTH Machines)**
  
   Since experiments often require switching between the Sepia and default kernels, we recommend keeping both presets in `/etc/default/grub` and toggling by uncommenting one pair at a time:
   ```bash
   # --- Sepia preset ---
   # GRUB_DEFAULT="1>Ubuntu, with Linux 6.6.41-sepia"
   # GRUB_CMDLINE_LINUX_DEFAULT="numa_cma=0:1G"

   # --- Baseline preset ---
   GRUB_DEFAULT="1>Ubuntu, with Linux 6.6.41-default"
   GRUB_CMDLINE_LINUX_DEFAULT=""
   ```
   ```bash
   update-grub
   reboot
   ```



## 2. Configure Passwordless SSH Between Two Machines

Many experiment scripts launch client-side commands from the server via `ssh`.
Without passwordless SSH, remote commands can block on password prompts and break automation.
Set up passwordless SSH first so one server-side script can orchestrate both machines end-to-end.

Assume:
- `<server_ip>` = server (runs orchestration scripts)
- `<client_ip>` = client (runs remote commands)
- remote user in scripts = `<client_user>` (replace with your account)

Before running commands below, replace all placeholders:
- `<server_ip>` with your server machine IP
- `<client_ip>` with your client machine IP
- `<client_user>` with your client login account

Example values (do not copy as-is):
- `<server_ip>`: `192.168.10.213`
- `<client_ip>`: `192.168.10.211`
- `<client_user>`: `sepia`

If you run experiment scripts as `root`, configure SSH keys as `root` on the server:
```bash
sudo -i
```

On `<server_ip>` (server), generate an SSH key if needed:
```bash
ssh-keygen -t ed25519
```

Copy the public key to the client account:
```bash
ssh-copy-id <client_user>@<client_ip>
```
Example:
```bash
ssh-copy-id sepia@192.168.10.211
```

Verify passwordless login:
```bash
ssh <client_user>@<client_ip> "echo SSH_OK"
```
Example:
```bash
ssh sepia@192.168.10.211 "echo SSH_OK"
```

Expected output:
```bash
SSH_OK
```

If your environment does not have `ssh-copy-id`, use:
```bash
cat ~/.ssh/id_ed25519.pub | ssh <client_user>@<client_ip> "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```
Example:
```bash
cat ~/.ssh/id_ed25519.pub | ssh sepia@192.168.10.211 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

## 3. Run Toy-experiments (with root)

This section validates that both kernels boot correctly and run the same toy workload.

### 3.1 Baseline (default kernel)
1. Set GRUB to the default kernel and reboot.
2. Verify the running kernel:
   ```bash
   uname -r
   ```
   Expected: 6.6.41-default (or your baseline kernel string).
3. Run the toy experiment on server:
   ```
   cd /usr/src/sepia/OSDI_26_artifact/toy_experiment/default
   /proc/sys/sepia_page_pool/sepia_init_flag_numa0
   ./run_experiment.sh
   ```
### 3.2 Sepia kernel
1. Set GRUB to the Sepia kernel preset (numa_cma=0:1G) and reboot.
2. Verify the running kernel:
   ```bash
   uname -r
   ```
   Expected: 6.6.41-sepia.
3. pre-setup on client(192.168.10.211)
   ```
   cd /usr/src/sepia/OSDI_26_artifact/toy_experiment/sepia
   ./sepia_with_no_aRFS.sh
   ```
4. Run the toy experiment on server:
   ```
   cd /usr/src/sepia/OSDI_26_artifact/toy_experiment/sepia
   ./run_experiment.sh
   ```


**To continue the artifact evaluation:** please go to OSDI_26_artifact/
