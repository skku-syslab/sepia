# Step 0: Setup the output directory.
mkdir -p data/address_list-default

# Step 1: Compile the generator.
g++ -o ./bin/gen_default_address_list.exe ./code/gen_default_address_list.cpp

# Step 2: Generate the address list.
sudo ls > /dev/null # Just get sudo permission
sudo bash -c '
for workingset_size_mb in 16 18 20 22 24 26 28 30 32 34 36; do
    echo "Default ${workingset_size_mb}MB start"
    ./bin/gen_default_address_list.exe $workingset_size_mb > /dev/null 2>&1 &
done
wait
'

wait
sudo chown -R $USER ./data
echo Done