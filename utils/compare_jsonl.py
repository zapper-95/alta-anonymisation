#!/usr/bin/env python3
"""
Compare two JSONL files: find indexes where file1 succeeded but file2 failed,
then rank by the largest confidence_score difference.
"""

import json
import argparse
import sys


def load_first_line(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.loads(f.readline())


def main():
    parser = argparse.ArgumentParser(
        description="Find top-N indexes where JSONL1 succeeded and JSONL2 failed, "
                    "sorted by confidence_score difference."
    )
    parser.add_argument("jsonl1", help="Path to the first JSONL file")
    parser.add_argument("jsonl2", help="Path to the second JSONL file")
    parser.add_argument("-n", "--top-n", type=int, default=50,
                        help="Number of top results to return (default: 10)")
    args = parser.parse_args()

    data1 = load_first_line(args.jsonl1)
    data2 = load_first_line(args.jsonl2)

    success1 = data1["success"]
    success2 = data2["success"]
    conf1 = data1["confidence_score"]
    conf2 = data2["confidence_score"]

    if len(success1) != len(success2):
        print(f"Error: mismatched lengths -- file1 has {len(success1)} entries, "
              f"file2 has {len(success2)}", file=sys.stderr)
        sys.exit(1)

    # Collect indexes where file1 is True and file2 is False
    candidates = []
    for i in range(len(success1)):
        if success1[i] and not success2[i] and conf1[i] >= 90:
            diff = abs(conf1[i] - conf2[i])
            candidates.append((i, conf1[i], conf2[i], diff))

    # Sort by confidence difference descending
    candidates.sort(key=lambda x: x[3], reverse=True)

    top = candidates[:args.top_n]

    print(f"Found {len(candidates)} indexes where file1=True, file2=False.")
    print(f"Top {min(args.top_n, len(top))} by confidence_score difference:\n")
    print(f"{'Rank':<6} {'Index':<8} {'Conf1':<10} {'Conf2':<10} {'Diff':<10}")
    print("-" * 44)

    for rank, (idx, c1, c2, diff) in enumerate(top, 1):
        print(f"{rank:<6} {idx:<8} {c1:<10.4f} {c2:<10.4f} {diff:<10.4f}")


if __name__ == "__main__":
    main()