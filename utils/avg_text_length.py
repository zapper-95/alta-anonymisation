import json
import sys

def average_text_length(filepath):
    total_chars = 0
    count = 0
    max_len = None
    min_len = None
    labels = set()

    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Skipping invalid JSON on line {line_num}: {e}", file=sys.stderr)
                continue

            text = obj.get("text")
            if text is None:
                continue
            if not isinstance(text, str):
                print(f"Skipping non-string 'text' on line {line_num}", file=sys.stderr)
                continue

            length = len(text)
            total_chars += length
            count += 1

            if max_len is None or length > max_len:
                max_len = length
            if min_len is None or length < min_len:
                min_len = length

            if "label" in obj:
                labels.add(obj["label"])

    if count == 0:
        print("No valid 'text' entries found.")
        return

    avg = total_chars / count
    print(f"Entries counted: {count}")
    print(f"Total characters: {total_chars}")
    print(f"Average length: {avg:.2f} characters")
    print(f"Max length: {max_len} characters")
    print(f"Min length: {min_len} characters")
    print(f"Unique labels: {len(labels)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python avg_text_length.py <path_to_jsonl>")
        sys.exit(1)

    average_text_length(sys.argv[1])