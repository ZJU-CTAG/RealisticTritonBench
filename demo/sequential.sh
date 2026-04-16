set -x

tasks=(39 44 49 50 53 54)

for i in "${tasks[@]}"; do
    echo "---------Running task $i---------"
    
    python eval.py --use_gold --task_id $i --skip_evaluation
    
    docker commit instance-$i-rtbench-instance-vllm-$i rtbench-instance-vllm-$i:v1
    
    echo "---------Finished task $i---------"
done