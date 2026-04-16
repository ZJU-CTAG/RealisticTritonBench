containers=(1 2 6 7 9 10 11 13 14 15 16 17 18 19 20 21 22 25 26 27 28 29 30 33 34 36 39 44 49 50 53 54)

for i in "${containers[@]}"; do
    docker stop instance-$i-rtbench-instance-vllm-$i
    docker rm instance-$i-rtbench-instance-vllm-$i
done