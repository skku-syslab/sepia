# Set this to the name of the interface on the NIC that should be used
# List of available interfaces can be obtained via `ifconfig`
# In our setup we use a 200Gbps NIC. Speed of an interface can be obtained via `ethtool <interface-name> | grep -i speed` 
IFACE="ens2np0"

# Set this to the IP address corresponding to the above interface
# This can be obtained via `ifconfig`
IP_ADDR="192.168.10.211"

# This is the IP address of the other machine 
# i.e. this is the value that you would enter in the IP_ADDR field in the config.sh file on the other machine
PEER_IP_ADDR="192.168.10.213"

# If you have an NVMe SSD attached to the machine, specify it's PCIe bus address here
# If there is not SSD, just set it to "none"
# One way to look for SSDs is to run `lspci | grep -i nvme`
SSD_ADDR="none"