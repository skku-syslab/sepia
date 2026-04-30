#!/bin/bash

REPEAT_COUNT=${1:-1}

max_num=0
for dir in one_flow_* two_flow_* three_flow_* four_flow_* five_flow_* six_flow_*; do
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

    # 1 flow test
    echo ""
    echo "[1/6] Running one flow test..."
    ./one_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ One flow test completed"
    else
        echo "✗ One flow test failed"
    fi
    sleep 3

    # 2 flow test
    echo ""
    echo "[2/6] Running two flow test..."
    ./two_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Two flow test completed"
    else
        echo "✗ Two flow test failed"
    fi
    sleep 3

    # 3 flow test
    echo ""
    echo "[3/6] Running three flow test..."
    ./three_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Three flow test completed"
    else
        echo "✗ Three flow test failed"
    fi
    sleep 3

    # 4 flow test
    echo ""
    echo "[4/6] Running four flow test..."
    ./four_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Four flow test completed"
    else
        echo "✗ Four flow test failed"
    fi
    sleep 3

    # 5 flow test
    echo ""
    echo "[5/6] Running five flow test..."
    ./five_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Five flow test completed"
    else
        echo "✗ Five flow test failed"
    fi
    sleep 3

    # 6 flow test
    echo ""
    echo "[6/6] Running six flow test..."
    ./six_flow_test.sh
    if [ $? -eq 0 ]; then
        echo "✓ Six flow test completed"
    else
        echo "✗ Six flow test failed"
    fi
    sleep 3

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
    echo "  - one_flow_${TEST_NUM}/"
    echo "  - two_flow_${TEST_NUM}/"
    echo "  - three_flow_${TEST_NUM}/"
    echo "  - four_flow_${TEST_NUM}/"
    echo "  - five_flow_${TEST_NUM}/"
    echo "  - six_flow_${TEST_NUM}/"
    
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