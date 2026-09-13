#!/usr/bin/env python3
"""
Sort a .jsonl file by a numeric field (default: "idx"), writing a new file
with "_sorted" appended before the extension. Does not modify the input.

Usage:
    python sort_jsonl.py input.jsonl                       # sort by "idx"
    python sort_jsonl.py input.jsonl --field id            # sort by another field
    python sort_jsonl.py input.jsonl -o custom_output.jsonl
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="path to input .jsonl")
    p.add_argument("--field", default="idx", help="field to sort by (default: idx)")
    p.add_argument("-o", "--output",
                   help="output path (default: <input>_sorted<ext>)")
    p.add_argument("--reverse", action="store_true", help="sort descending")
    args = p.parse_args()

    in_path = Path(args.input)
    if not in_path.is_file():
        sys.exit(f"ERROR: input not found: {in_path}")

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = in_path.with_name(in_path.stem + "_sorted" + in_path.suffix)

    if out_path.resolve() == in_path.resolve():
        sys.exit("ERROR: output path equals input path; refusing to overwrite")

    # read all records, remembering original line for stable error reporting
    records = []
    missing_field = 0
    with open(in_path, encoding="utf-8") as f:
        for ln, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                sys.exit(f"ERROR: bad JSON on line {ln}: {e}")
            if args.field not in rec:
                missing_field += 1
                # keep it, but it'll sort with a placeholder key
            records.append(rec)

    if missing_field:
        sys.exit(f"ERROR: {missing_field}/{len(records)} record(s) missing "
                 f"'{args.field}' field; aborting so nothing is silently dropped")

    # sort
    def sort_key(r):
        v = r[args.field]
        # numeric-first sort: try to coerce, fall back to string
        try:
            return (0, float(v))
        except (TypeError, ValueError):
            return (1, str(v))

    records.sort(key=sort_key, reverse=args.reverse)

    # write
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Sorted {len(records)} records by '{args.field}'"
          f"{' (descending)' if args.reverse else ''}")
    print(f"  in : {in_path}")
    print(f"  out: {out_path}")


if __name__ == "__main__":
    main()
