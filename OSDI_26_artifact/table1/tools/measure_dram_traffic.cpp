#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <linux/perf_event.h>
#include <perfmon/pfmlib.h>
#include <perfmon/pfmlib_perf_event.h>
#include <signal.h>
#include <time.h>

const int num_imc = 12;
// One triplet of counters per IMC: total / read / write CAS commands.
int fd_data_total[num_imc];
int fd_data_read[num_imc];
int fd_data_write[num_imc];
// Used to compute elapsed measurement time.
struct timespec t_start, t_end;

void sigint_handler(int signal) {
    // On Ctrl+C: stop counting, read all IMC counters, then print bandwidth.
    clock_gettime(CLOCK_MONOTONIC, &t_end);
    double elapsed = (t_end.tv_sec - t_start.tv_sec) +
                    (t_end.tv_nsec - t_start.tv_nsec) / 1e9;
    printf("Measurement_time: %.3f sec\n", elapsed);
    ssize_t res;
    for(int imc=0; imc<num_imc; imc++) {
        ioctl(fd_data_total[imc], PERF_EVENT_IOC_DISABLE, 0);
        ioctl(fd_data_read[imc], PERF_EVENT_IOC_DISABLE, 0);
        ioctl(fd_data_write[imc], PERF_EVENT_IOC_DISABLE, 0);
    }
    long long data_total[num_imc];
    long long data_read[num_imc];
    long long data_write[num_imc];
    double data_miss_rate[num_imc];
    for(int imc=0; imc<num_imc; imc++) {
        // Read raw counter values (number of CAS commands).
        res = read(fd_data_total[imc], &data_total[imc], sizeof(data_total[imc]));
        res = read(fd_data_read[imc], &data_read[imc], sizeof(data_read[imc]));
        res = read(fd_data_write[imc], &data_write[imc], sizeof(data_write[imc]));
    }

    long long total_data_total = 0;
    long long total_data_read = 0;
    long long total_data_write = 0;
    for(int imc=0; imc<num_imc; imc++)
        {
            // Optional: uncomment the prints below to see per-IMC counter values.
            // printf("imc%d_data-total:%lld\n", imc, data_total[imc]);
            // printf("imc%d_data-read:%lld\n", imc, data_read[imc]);
            // printf("imc%d_data-write:%lld\n", imc, data_write[imc]);

        total_data_total += data_total[imc];
        total_data_read += data_read[imc];
        total_data_write += data_write[imc];

        close(fd_data_total[imc]);
        close(fd_data_read[imc]);
        close(fd_data_write[imc]);
    }

    // Convert CAS counts to bandwidth (assumes 64 bytes per CAS) and report MB/s.
    printf("total_bw: %.4lf MB/s\n", (double)(total_data_total * 64) / (1024 * 1024 * elapsed));
    printf("read_bw: %.4lf MB/s\n", (double)(total_data_read * 64) / (1024 * 1024 * elapsed));
    printf("write_bw: %.4lf MB/s\n", (double)(total_data_write * 64) / (1024 * 1024 * elapsed));
    pfm_terminate();
    exit(0);
}

int open_counter_fd(char event_str[], int imc) {
    int ret;
    struct perf_event_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.size = sizeof(attr);

    pfm_perf_encode_arg_t arg;
    memset(&arg, 0, sizeof(arg));
    arg.attr = &attr;

    // Encode the libpfm event string into perf_event_attr.
    ret = pfm_get_os_event_encoding(event_str,
                                    PFM_PLM0 | PFM_PLM3,
                                    PFM_OS_PERF_EVENT_EXT,
                                    &arg);
    if (ret != PFM_SUCCESS) {
        fprintf(stderr, "Encoding failed for imc%d: %s\n",
                imc, pfm_strerror(ret));
        exit(-1);
    }

    // pid=-1 opens a system-wide event; IMC tiles are not tied to CPU affinity.
    int fd = perf_event_open(&attr, -1, 0, -1, 0);
    if (fd < 0) {
        perror("perf_event_open");
        exit(-1);
    }

    return fd;
}

void start() {
    // Reset and enable all counters, then wait until SIGINT.
    for(int imc=0; imc<num_imc; imc++) {
        ioctl(fd_data_total[imc], PERF_EVENT_IOC_RESET, 0);
        ioctl(fd_data_total[imc], PERF_EVENT_IOC_ENABLE, 0);
        ioctl(fd_data_read[imc], PERF_EVENT_IOC_RESET, 0);
        ioctl(fd_data_read[imc], PERF_EVENT_IOC_ENABLE, 0);
        ioctl(fd_data_write[imc], PERF_EVENT_IOC_RESET, 0);
        ioctl(fd_data_write[imc], PERF_EVENT_IOC_ENABLE, 0);
    }
    
    printf("Running... Press Ctrl+C to stop.\n");
    clock_gettime(CLOCK_MONOTONIC, &t_start);
    while (1) {
        pause();   // Wait for SIGINT (Ctrl+C).
    }
}

int main() {
    // Initialize libpfm so we can translate event strings to perf_event_attr.
    int ret = pfm_initialize();
    if (ret != PFM_SUCCESS) {
        fprintf(stderr, "pfm_initialize failed: %s\n", pfm_strerror(ret));
        return 1;
    }

    // Ctrl+C triggers reporting and cleanup.
    signal(SIGINT, sigint_handler);

    for (int imc = 0; imc < num_imc; imc++) {
        char event_str[128];
        // Open three CAS counters per IMC: ALL / RD / WR.
        snprintf(event_str, sizeof(event_str),
                 "icx_unc_imc%d::UNC_M_CAS_COUNT:ALL", imc);
        fd_data_total[imc] = open_counter_fd(event_str, imc);
        snprintf(event_str, sizeof(event_str),
                 "icx_unc_imc%d::UNC_M_CAS_COUNT:RD", imc);
        fd_data_read[imc] = open_counter_fd(event_str, imc);
        snprintf(event_str, sizeof(event_str),
                 "icx_unc_imc%d::UNC_M_CAS_COUNT:WR", imc);
        fd_data_write[imc] = open_counter_fd(event_str, imc);

        // Keep counters disabled until start() begins the measurement window.
        ioctl(fd_data_total[imc], PERF_EVENT_IOC_DISABLE, 0);
        ioctl(fd_data_read[imc], PERF_EVENT_IOC_DISABLE, 0);
        ioctl(fd_data_write[imc], PERF_EVENT_IOC_DISABLE, 0);
    }

    start();

    return 0;
}