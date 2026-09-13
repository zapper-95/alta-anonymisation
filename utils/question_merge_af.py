#!/usr/bin/env python3
"""Merge question fields from a second JSONL file into a first, line by line.

Usage:
    python merge_question_format.py first.jsonl second.jsonl

Lines are assumed to correspond positionally. Each pair is checked with
first["username"] == second["id"]; mismatches are reported and skipped.
Output: <first_stem>_question_format.jsonl next to the first file.
"""

import json
import sys
from itertools import zip_longest
from pathlib import Path

FIELDS = ("question", "choices", "answer", "answer_indx")


def main():
    if len(sys.argv) != 3:
        sys.exit(f"usage: {Path(sys.argv[0]).name} FIRST.jsonl SECOND.jsonl")

    first_path = Path(sys.argv[1])
    second_path = Path(sys.argv[2])
    out_path = first_path.with_name(f"{first_path.stem}_question_format.jsonl")

    written = 0
    skipped = 0

    with open(first_path, encoding="utf-8") as f1, open(second_path, encoding="utf-8") as f2, open(out_path, "w", encoding="utf-8") as out:
        for lineno, (l1, l2) in enumerate(zip_longest(f1, f2), start=1):
            if l1 is None or l2 is None:
                which = "first" if l1 is None else "second"
                print(f"line {lineno}: {which} file ended early - stopping",
                      file=sys.stderr)
                break

            l1, l2 = l1.strip(), l2.strip()
            if not l1 or not l2:
                continue

            try:
                rec = json.loads(l1)
                q = json.loads(l2)
            except json.JSONDecodeError as e:
                print(f"line {lineno}: bad JSON ({e}) - skipping", file=sys.stderr)
                skipped += 1
                continue

            if int(rec.get("username")) != q.get("id"):
                print(f"line {lineno}: mismatch username={rec.get('username')!r} "
                      f"vs id={q.get('id')!r} - skipping", file=sys.stderr)
                skipped += 1
                continue

            missing = [k for k in FIELDS if k not in q]
            if missing:
                print(f"line {lineno}: second file missing {missing} - skipping",
                      file=sys.stderr)
                skipped += 1
                continue

            rec.update({k: q[k] for k in FIELDS})
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1

    print(f"wrote {written} lines to {out_path} ({skipped} skipped)")


if __name__ == "__main__":
    main()