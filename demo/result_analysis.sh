# Deepseek-chat

python demo/res_analysis.py --model-name ds_chat

python demo/aggregate_metrics.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --output demo/logs/res_analysis_ds_chat_avg_metrics.json
  
python /home/jinjunhuang/RTBench/RTBench/demo/calc_success_ratio.py \
  --input /home/jinjunhuang/RTBench/RTBench/demo/logs/res_analysis_ds_chat.json \
  --output /home/jinjunhuang/RTBench/RTBench/demo/logs/success_ratio_ds_chat.json
  
python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --task-type modificaton

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --task-type new_op

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --task-type optimization

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --output demo/logs/success_ratio_ds_chat.json \
  --task-type modificaton

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --output demo/logs/success_ratio_ds_chat.json \
  --task-type new_op

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_chat.json \
  --output demo/logs/success_ratio_ds_chat.json \
  --task-type optimization

# Deepseek-reasoner

python demo/res_analysis.py --model-name ds_reasoner

python demo/aggregate_metrics.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --output demo/logs/res_analysis_ds_reasoner_avg_metrics.json
  
python /home/jinjunhuang/RTBench/RTBench/demo/calc_success_ratio.py \
  --input /home/jinjunhuang/RTBench/RTBench/demo/logs/res_analysis_ds_reasoner.json \
  --output /home/jinjunhuang/RTBench/RTBench/demo/logs/success_ratio_ds_reasoner.json

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --task-type modificaton

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --task-type new_op

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --task-type optimization

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --output demo/logs/success_ratio_ds_reasoner.json \
  --task-type modificaton

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --output demo/logs/success_ratio_ds_reasoner.json \
  --task-type new_op

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_ds_reasoner.json \
  --output demo/logs/success_ratio_ds_reasoner.json \
  --task-type optimization

# Qwen

python demo/res_analysis.py --model-name qwen --output demo/logs/res_analysis_qwen.json

python demo/aggregate_metrics.py \
  --input demo/logs/res_analysis_qwen.json \
  --output demo/logs/res_analysis_qwen_avg_metrics.json

python /home/jinjunhuang/RTBench/RTBench/demo/calc_success_ratio.py \
  --input /home/jinjunhuang/RTBench/RTBench/demo/logs/res_analysis_qwen.json \
  --output /home/jinjunhuang/RTBench/RTBench/demo/logs/success_ratio_qwen.json

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --task-type modificaton

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --task-type new_op

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --task-type optimization

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --output demo/logs/success_ratio_qwen.json \
  --task-type modificaton

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --output demo/logs/success_ratio_qwen.json \
  --task-type new_op

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_qwen.json \
  --output demo/logs/success_ratio_qwen.json \
  --task-type optimization

# GPT

python demo/res_analysis.py --model-name gpt

python demo/aggregate_metrics.py \
  --input demo/logs/res_analysis_gpt.json \
  --output demo/logs/res_analysis_gpt_avg_metrics.json

python /home/jinjunhuang/RTBench/RTBench/demo/calc_success_ratio.py \
  --input /home/jinjunhuang/RTBench/RTBench/demo/logs/res_analysis_gpt.json \
  --output /home/jinjunhuang/RTBench/RTBench/demo/logs/success_ratio_gpt.json

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --task-type modificaton

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --task-type new_op

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --task-type optimization

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --output demo/logs/success_ratio_gpt.json \
  --task-type modificaton

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --output demo/logs/success_ratio_gpt.json \
  --task-type new_op

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gpt.json \
  --output demo/logs/success_ratio_gpt.json \
  --task-type optimization

# Gemini

python demo/res_analysis.py --model-name gemini

python demo/aggregate_metrics.py \
  --input demo/logs/res_analysis_gemini.json \
  --output demo/logs/res_analysis_gemini_avg_metrics.json

python /home/jinjunhuang/RTBench/RTBench/demo/calc_success_ratio.py \
  --input /home/jinjunhuang/RTBench/RTBench/demo/logs/res_analysis_gemini.json \
  --output /home/jinjunhuang/RTBench/RTBench/demo/logs/success_ratio_gemini.json

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --task-type modificaton

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --task-type new_op

python demo/aggregate_metrics_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --task-type optimization

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --output demo/logs/success_ratio_gemini.json \
  --task-type modificaton

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --output demo/logs/success_ratio_gemini.json \
  --task-type new_op

python demo/calc_success_ratio_type.py \
  --input demo/logs/res_analysis_gemini.json \
  --output demo/logs/success_ratio_gemini.json \
  --task-type optimization