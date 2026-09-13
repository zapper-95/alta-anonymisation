import json
import sys

def reindex(path):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    with open(path, "w", encoding="utf-8") as f:
        for i, line in enumerate(lines):
            obj = json.loads(line)
            obj["id"] = str(i)
            f.write(json.dumps(obj) + "\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python reindex.py <file.jsonl>")
        sys.exit(1)
    reindex(sys.argv[1])