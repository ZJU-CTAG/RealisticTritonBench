from openai import OpenAI
import os

client = OpenAI(
    # 如果没有配置环境变量，请用阿里云百炼API Key替换：api_key="sk-xxx"
    api_key="sk-xAkdPXxYaLp8JwzVE85K1jvYB9vRVhkTrFXAWH3LoAXhpjgP",
    base_url="https://xiaoai.plus/v1",
)

messages = [{"role": "user", "content": "你是谁"}]
completion = client.chat.completions.create(
    model="gemini-3.1-pro-preview",  
    messages=messages,
    stream=False
)

print(completion.choices[0].message)


