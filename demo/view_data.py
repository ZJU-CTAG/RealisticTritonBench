import json

DATA_PATH = "../data/filter_dataset.jsonl"

with open(DATA_PATH, "r") as f:
    data_list = [json.loads(line) for line in f]

number = 29720

for data in data_list:
    if data["pull_number"] == number:
        print(json.dumps(data, indent=2))

