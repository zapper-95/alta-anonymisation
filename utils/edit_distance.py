#!/usr/bin/env python3
"""
Compare "text" (original) to "final_text" (anonymised) per line of a JSONL file.
Writes a CSV of per-document scores next to the input file, and prints the
column averages to stdout.

Usage:
    python3 edit_distance.py file.jsonl

Output:
    file.csv   (same folder, same basename)
    columns: doc_index, char_lev, char_lev_norm, word_lev, word_lev_norm,
             token_ratio, jaccard

Lower Levenshtein / higher token_ratio+jaccard = closer to the original.
Levenshtein is confounded by output length; jaccard and token_ratio are
length-robust and reflect shared content, so weigh those.
"""
import sys
import os
import csv
import json
import difflib


def char_levenshtein(a, b):
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return max(m, n)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ai = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def word_levenshtein(a, b):
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return max(m, n)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ai = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def jaccard(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


FIELDS = ["doc_index", "char_lev", "char_lev_norm",
          "word_lev", "word_lev_norm", "token_ratio", "jaccard"]


def main():
    if len(sys.argv) != 2:
        print("usage: python3 edit_distance.py file.jsonl", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    out_path = os.path.splitext(path)[0] + ".csv"

    rows = []
    skipped = 0
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            print(lineno)
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                print(f"[warn] line {lineno}: bad JSON, skipping", file=sys.stderr)
                skipped += 1
                continue
            if "text" not in obj or "final_text" not in obj:
                print(f"[warn] line {lineno}: missing 'text'/'final_text', skipping", file=sys.stderr)
                skipped += 1
                continue

            orig = obj["text"] or ""
            anon = obj["final_text"] or ""
            ow, aw = orig.split(), anon.split()

            cl = char_levenshtein(orig, anon)
            wl = word_levenshtein(ow, aw)
            rows.append({
                "doc_index": len(rows),
                "char_lev": cl,
                "char_lev_norm": round(cl / max(len(orig), len(anon), 1), 4),
                "word_lev": wl,
                "word_lev_norm": round(wl / max(len(ow), len(aw), 1), 4),
                "token_ratio": round(difflib.SequenceMatcher(None, ow, aw).ratio(), 4),
                "jaccard": round(jaccard([w.lower() for w in ow], [w.lower() for w in aw]), 4),
            })

    if not rows:
        print(f"no usable lines ({skipped} skipped); no CSV written.", file=sys.stderr)
        sys.exit(1)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    print(f"wrote {out_path}  ({n} docs" + (f", {skipped} skipped" if skipped else "") + ")")
    print("averages:")
    for k in FIELDS[1:]:
        print(f"  {k:15s} {sum(r[k] for r in rows) / n:.4f}")


if __name__ == "__main__":
    main()