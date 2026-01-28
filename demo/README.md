# RTBench 评估系统

这是一个用于评估代码优化任务的完整系统，基于 Docker 容器化环境。

## 系统架构

评估流程包括以下主要步骤：

1. **基础镜像构建**: 根据 `base_tag` 为每个 vLLM 版本构建基础 Docker 镜像
2. **最终镜像构建**: 在基础镜像上拉取对应的 PR 并将 `new_func` 替换回 `source_func`
3. **模型推理**: 使用任务描述、上下文和函数信息构建 Prompt，让模型生成优化后的函数
4. **代码替换**: 在容器中将模型生成的函数替换到相应位置
5. **测试执行**: 运行指定的测试脚本并收集结果

## 数据格式

数据集使用 `problems.json` 格式，每个任务包含以下字段：

```json
{
  "task_id": "任务标识符",
  "name": "任务名称", 
  "type": "任务类型（如 optimization）",
  "task_description": "任务描述",
  "targets": {
    "文件名": {
      "path": "文件路径",
      "functions": ["函数名列表"],
      "source_func": {"函数名": "原始函数代码"},
      "new_func": {"函数名": "修改后的函数代码"}
    }
  },
  "context": {
    "文件名": "上下文代码"
  },
  "test_scripts": {
    "测试名": "测试命令"
  },
  "base_tag": "基础版本标签",
  "pull_number": "PR编号",
  "repo": "仓库名",
  "hardware": "硬件类型"
}
```

## 使用方法

### 基本用法

```bash
python main.py --model <模型名称> --task_id <任务ID>
```

### 参数说明

- `--model`: 要使用的模型名称或路径（必需）
- `--dataset_path`: 数据集文件路径（默认: ../problems.json）
- `--task_id`: 要评估的任务ID列表（可选，不指定则评估所有任务）

### 示例

```bash
# 评估单个任务
python main.py --model gpt-4 --task_id 0

# 评估多个任务
python main.py --model claude-3 --task_id 0 1 2

# 使用自定义数据集
python main.py --model llama-2 --dataset_path ./my_problems.json
```

## 环境要求

### Python 依赖

```bash
pip install docker
pip install argparse
pip install pathlib
```

### Docker 要求

- Docker Engine 已安装并运行
- 当前用户有 Docker 权限
- 足够的磁盘空间用于构建镜像

### 系统要求

- Linux 系统（推荐）
- 至少 8GB RAM
- 至少 50GB 可用磁盘空间

## 目录结构

```
RTBench/demo/
├── main.py              # 主评估脚本
├── test_main.py         # 测试脚本
├── utils/
│   ├── utils.py         # 工具函数
│   └── constants.py     # 常量定义
├── results/             # 结果输出目录（自动创建）
└── README.md           # 本文件
```

## 输出结果

评估结果会保存在 `results/` 目录下，每个任务生成一个 JSON 文件：

```json
{
  "task_id": "任务ID",
  "test_results": {
    "测试名": {
      "exit_code": 0,
      "output": "测试输出",
      "success": true
    }
  },
  "success": true,
  "error": null
}
```

## 注意事项

1. **Docker 权限**: 确保当前用户有 Docker 操作权限
2. **网络连接**: 需要稳定的网络连接来拉取 Docker 基础镜像和 Git 仓库
3. **磁盘空间**: 每个基础镜像约需要 2-5GB 空间
4. **模型集成**: 当前模型调用是占位符实现，需要集成具体的模型 API
5. **错误处理**: 系统会跳过失败的任务并继续处理其他任务

## 扩展功能

### 添加新的模型

在 `generate_function_with_model()` 函数中添加新的模型调用逻辑。

### 自定义测试脚本

在数据集的 `test_scripts` 字段中定义自定义测试命令。

### 结果分析

可以编写脚本来分析 `results/` 目录中的 JSON 结果文件。

## 故障排除

### 常见问题

1. **Docker 权限错误**: 运行 `sudo usermod -aG docker $USER` 并重新登录
2. **磁盘空间不足**: 使用 `docker system prune` 清理未使用的镜像
3. **网络超时**: 检查网络连接或使用镜像代理
4. **构建失败**: 检查 Dockerfile 语法和依赖版本

### 日志查看

系统会输出详细的运行日志，包括：
- 镜像构建过程
- 函数替换结果
- 测试执行输出
- 错误信息

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个评估系统。

## 许可证

本项目遵循 MIT 许可证。