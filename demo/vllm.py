import torch
import time

# 保存每个 GPU 的 tensor
gpu_tensors = {}
gpu_reserved = {}

num_gpus = torch.cuda.device_count()

for i in range(num_gpus):
    gpu_tensors[i] = []
    gpu_reserved[i] = 0

print(f"Detected {num_gpus} GPUs")

while True:
    for i in range(num_gpus):
        device = f"cuda:{i}"

        free_mem, total_mem = torch.cuda.mem_get_info(i)

        print(f"GPU {i}: Free Memory: {free_mem/1024**3:.2f} GB, Total Memory: {total_mem/1024**3:.2f} GB")

        target_mem = int(free_mem * 0.95)

        need_mem = target_mem - gpu_reserved[i]

        if need_mem > 0:
            num_elements = need_mem // 4  # float32 = 4 bytes

            try:
                tensor = torch.empty(num_elements, dtype=torch.float32, device=device)
                gpu_tensors[i].append(tensor)

                gpu_reserved[i] += num_elements * 4

                print(
                    f"GPU {i}: add {(num_elements*4)/1024**3:.2f} GB, "
                    f"total {gpu_reserved[i]/1024**3:.2f} GB"
                )
            except RuntimeError:
                pass
        

    time.sleep(5)