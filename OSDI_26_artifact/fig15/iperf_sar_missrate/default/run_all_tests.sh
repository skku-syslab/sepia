#!/bin/bash


REPEAT_COUNT=${1:-1}

max_num=0
for dir in eight_flow_* ten_flow_* twelve_flow_* fourteen_flow_* sixteen_flow_* eighteen_flow_*; do
    if [ -d "$dir" ]; then
        num=$(echo "$dir" | sed 's/.*_\([0-9]*\)$/\1/')
        if [ -n "$num" ] && [ "$num" -gt "$max_num" ]; then
            max_num=$num
        fi
    fi
done
START_NUM=$((max_num + 1))

echo "========================================"
echo "Starting all flow tests"
echo "Will run ${REPEAT_COUNT} iteration(s)"
echo "Starting from test #${START_NUM}"
echo "========================================"

total_start_time=$(date +%s)

for ((iteration=0; iteration<REPEAT_COUNT; iteration++)); do
    TEST_NUM=$((START_NUM + iteration))
    export TEST_NUM
    
    echo ""
    echo "========================================"
    echo "ITERATION $((iteration + 1))/${REPEAT_COUNT}"
    echo "Test Run #${TEST_NUM}"
    echo "========================================"
    
    start_time=$(date +%s)

    # 8 flow test
    echo ""
    echo "[1/6] Running eight flow test..."
    ./eight_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Eight flow test completed"
    else
        echo "✗ Eight flow test failed"
    fi
    sleep 3

    # 10 flow test
    echo ""
    echo "[2/6] Running ten flow test..."
    ./ten_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Ten flow test completed"
    else
        echo "✗ Ten flow test failed"
    fi
    sleep 3

    # 12 flow test
    echo ""
    echo "[3/6] Running twelve flow test..."
    ./twelve_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Twelve flow test completed"
    else
        echo "✗ Twelve flow test failed"
    fi
    sleep 3

    # 14 flow test
    echo ""
    echo "[4/6] Running fourteen flow test..."
    ./fourteen_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Fourteen flow test completed"
    else
        echo "✗ Fourteen flow test failed"
    fi
    sleep 3

    # 16 flow test
    echo ""
    echo "[5/6] Running sixteen flow test..."
    ./sixteen_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Sixteen flow test completed"
    else
        echo "✗ Sixteen flow test failed"
    fi
    sleep 3

    # 18 flow test
    echo ""
    echo "[6/6] Running eighteen flow test..."
    ./eighteen_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Eighteen flow test completed"
    else
        echo "✗ Eighteen flow test failed"
    fi
    sleep 3

    echo "All tests completed"

    end_time=$(date +%s)
    elapsed=$((end_time - start_time))
    minutes=$((elapsed / 60))
    seconds=$((elapsed % 60))

    echo ""
    echo "========================================"
    echo "Iteration $((iteration + 1))/${REPEAT_COUNT} completed!"
    echo "Test Run #${TEST_NUM}"
    echo "Time: ${minutes}m ${seconds}s"
    echo "========================================"
    echo "Results saved in:"
    echo "  - eight_flow_${TEST_NUM}/"
    echo "  - ten_flow_${TEST_NUM}/"
    echo "  - twelve_flow_${TEST_NUM}/"
    echo "  - fourteen_flow_${TEST_NUM}/"
    echo "  - sixteen_flow_${TEST_NUM}/"
    echo "  - eighteen_flow_${TEST_NUM}/"
    
    if [ $((iteration + 1)) -lt $REPEAT_COUNT ]; then
        echo ""
        echo "Waiting 5 seconds before next iteration..."
        sleep 5
    fi
done

total_end_time=$(date +%s)
total_elapsed=$((total_end_time - total_start_time))
total_minutes=$((total_elapsed / 60))
total_seconds=$((total_elapsed % 60))

echo ""
echo "========================================"
echo "ALL TESTS COMPLETED!"
echo "Total iterations: ${REPEAT_COUNT}"
echo "Test runs: #${START_NUM} ~ #$((START_NUM + REPEAT_COUNT - 1))"
echo "Total time: ${total_minutes}m ${total_seconds}s"
echo "========================================"