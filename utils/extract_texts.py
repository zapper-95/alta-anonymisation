import json
import os
import re
import sys

def sanitize_filename(name):
    """Remove or replace characters that aren't safe for filenames."""
    print(name)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return name.strip().rstrip('.')

def extract_texts(input_file, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)

    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Skipping line {i}: invalid JSON")
                continue

            name = record.get("wiki_name",None)
            if name == None:
                name=str(record.get("id"))

            final_text = record.get("final_text")

            if name is None or final_text is None:
                print(f"Skipping line {i}: missing 'wiki_name' or 'final_text'")
                continue

            filename = sanitize_filename(name) + ".txt"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as out:
                out.write(final_text)

            print(f"Wrote: {filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_texts.py <input.jsonl> [output_dir]")
        sys.exit(1)
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else f"./my_texts/{os.path.basename(sys.argv[1])}"
    extract_texts(input_file, output_dir)