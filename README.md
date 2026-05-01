# When DDIO Meets Page Coloring: Revisiting DDIO Performance with Sepia

**Sepia** is a novel color-aware page allocator for CPU-efficient network I/O processing. The performance of Intel's Data Direct I/O (DDIO) is often constrained by the "leaky DMA" problem, where packet data is evicted from the last-level cache (LLC) before processing completes. Our analysis reveals that conflict misses, rather than capacity limitations alone, are the primary cause of these LLC misses. 

**Sepia** minimizes LLC misses by leveraging a deeper understanding of sliced LLC architecture through its **Sepia** Manager, which constructs per-core colored page pools, and the **Sepia** Allocator, which employs a low-conflict, stride-1 allocation pattern.

Implemented in the Linux kernel and evaluated on SPDK, Nginx, and Memcached, **Sepia** achieves up to 1.51x higher throughput than the default Linux stack and saturates a 200Gbps link using 2.5 fewer CPU cores.


## Repository Overview

This repository includes the Sepia implementation for the Linux kernel and the reproduction scripts for the OSDI'26 Artifact Evaluation:

- `kernel_patch/`: Contains the Sepia core implementation (Sepia Manager and Sepia Allocator) and the baseline configuration for Linux kernel 6.6.
- `experiments/`: Includes automated scripts to reproduce evaluation results presented in the paper, including microbenchmarks and real-world applications. 


## Getting Started Guide

We assume a testbed consisting of two physical machines directly connected via a 200Gbps link to focus on CPU-bottleneck scenarios. Both machines are required to (1) be equipped with Intel Ice Lake processors to leverage the sliced LLC architecture, (2) have an NVIDIA ConnectX-6 (200Gbps) NIC installed , and (3) run Ubuntu 20.04 with Linux kernel 6.6.

This guide consists of three parts:
1. **Build and Install the Sepia Kernel and Default Kernel**

   Compile the Linux kernel 6.6 with Sepia modifications and enable the Contiguous Memory Allocator (CMA).

2. Configure Passwordless SSH Between Two Machines

3. Run Toy-experiments




## 1. Build and Install Kernels (on BOTH Machines) (with root)

Our evaluation requires two physical machines connected via a 200Gbps link. You must perform the following installation steps on both machines to ensure the entire testbed is consistent.

This repository contains source code for Sepia (Manager, Allocator, and NIC driver modifications) based on Linux kernel 6.6.41.

- Baseline: Install the Default kernel (with minimal tracing patches).
- Evaluation: Install the Sepia-patched kernel.

  Note: For each machine, we recommend building the kernels in /usr/src to maintain a consistent environment.


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
The Sepia kernel implements the color-aware page allocator within the mm/ directory and integrates it with the NIC driver.

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
- **Option A: Sepia Kernel (Evaluation)**

Sepia requires CMA reservation to manage colored pages. We reserve 1GB on NUMA node 0 for maximum stability and performance.

Note: Although 288MB is the minimum for 18 cores, 1GB ensures sufficient headroom for the system.

```bash
GRUB_DEFAULT="1>Ubuntu, with Linux 6.6.41-sepia"
GRUB_CMDLINE_LINUX_DEFAULT="numa_cma=0:1G"
```

- **Option B: Default Kernel (Baseline)**
Standard configuration without CMA reservation.
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
   ./enable_arfs_2.sh
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