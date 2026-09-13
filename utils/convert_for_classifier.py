import json
import argparse
import os

COLUMN_MAP = {
    "text": "text",
    "l1": "l1",
    "l2": "l2",
    "l3": "l3",
    "wiki_name": "wiki_name",
    "word_count": "word_count",
    "label": "label",
    "people": "people",
    "final_text": "anonymised_text",
    "candidate_list": "candidate_list"
}

parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input JSON file")
args = parser.parse_args()

folder, filename = os.path.split(args.input)
output = os.path.join(folder, f"CLEAN_text")
output = os.path.splitext(output)[0] + ".jsonl"

with open(args.input, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError:
        f.seek(0)
        data = [json.loads(line) for line in f if line.strip()]

with open(output, "w", encoding="utf-8") as f:
    for item in data:
        row = {out_key: item.get(in_key, "") for in_key, out_key in COLUMN_MAP.items()}
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

print(f"Done — wrote {len(data)} lines to {output}")