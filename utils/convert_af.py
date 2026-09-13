#!/usr/bin/env python3
"""
Convert a medqa-style iteration file into the standard {id, text, final_text}
format that convert_dataset.py / run_eval.sh expects.

Each source document has:
  {
    "username": "<id>",
    "comments": [                      # LIST OF ITERATIONS
      {                                # iteration 0: original
        "comments": [{"text": <ORIGINAL>, ...}],
        ...
      },
      {                                # iteration 1: first rewrite
        "comments": [{"text": <REWRITE_1>, ...}],
        ...
      },
      ...
    ],
    ...
  }

We pick iteration 0 as the ORIGINAL and iteration `iters` as the FINAL rewrite.

Usage:
    python convert_medqa_iters.py input.jsonl output.jsonl --iters 5
    python convert_medqa_iters.py input.jsonl output.jsonl --iters -1  # last available
"""
import argparse
import json
import sys


def extract_text(iteration):
    """Pull the vignette text out of one iteration entry.
    Structure: iteration["comments"][0]["text"]
    """
    inner = iteration.get("comments") or []
    if not inner:
        return None
    first = inner[0]
    return first.get("text") if isinstance(first, dict) else None


def convert(in_path, out_path, iters):
    n_in = n_out = n_skipped = 0
    seen_ids = set()

    with open(in_path, encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
        for ln, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            n_in += 1

            try:
                doc = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[warn] line {ln}: bad JSON, skipping ({e})", file=sys.stderr)
                n_skipped += 1
                continue

            # ---- id ----
            if "username" not in doc:
                print(f"[warn] line {ln}: no 'username' field, skipping", file=sys.stderr)
                n_skipped += 1
                continue
            raw_id = doc["username"]
            try:
                rid = int(raw_id)
            except (TypeError, ValueError):
                rid = raw_id  # keep string if not int-convertible

            if rid in seen_ids:
                sys.exit(f"ERROR: line {ln} has duplicate id {rid!r}. Ids must be unique.")
            seen_ids.add(rid)

            # ---- iteration list ----
            iterations = doc.get("comments") or []
            if not iterations:
                print(f"[warn] line {ln} (id={rid}): empty 'comments' list, skipping",
                      file=sys.stderr)
                n_skipped += 1
                continue

            # original = iteration 0
            orig = extract_text(iterations[0])
            if not orig or not orig.strip():
                print(f"[warn] line {ln} (id={rid}): no original text at iter 0, skipping",
                      file=sys.stderr)
                n_skipped += 1
                continue

            # final rewrite = iteration `iters`
            if iters == -1:
                target_idx = len(iterations) - 1
            else:
                target_idx = iters

            if target_idx < 0 or target_idx >= len(iterations):
                print(f"[warn] line {ln} (id={rid}): iters={iters} out of range "
                      f"(doc has {len(iterations)} iterations 0..{len(iterations)-1}), skipping",
                      file=sys.stderr)
                n_skipped += 1
                continue
            if target_idx == 0:
                print(f"[warn] line {ln} (id={rid}): iters={iters} points at the original "
                      f"(iteration 0) \u2014 final_text would equal text; skipping",
                      file=sys.stderr)
                n_skipped += 1
                continue

            final = extract_text(iterations[target_idx])
            if not final or not final.strip():
                print(f"[warn] line {ln} (id={rid}): iteration {target_idx} has no text, "
                      f"skipping", file=sys.stderr)
                n_skipped += 1
                continue

            out_rec = {"id": rid, "text": orig, "final_text": final}

            # Carry through anything else that might be useful downstream.
            for k in ("question", "choices", "answer", "answer_indx"):
                if k in doc:
                    out_rec[k] = doc[k]

            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            n_out += 1

    print(f"Read {n_in} -> wrote {n_out} (skipped {n_skipped}).")
    print(f"  original    <- iteration 0")
    print(f"  final_text  <- iteration {'last' if iters == -1 else iters}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("output")
    p.add_argument("--iters", type=int, required=True,
                   help="iteration index to use as final_text (0=original; "
                        "-1=last available; N=the Nth rewrite)")
    a = p.parse_args()
    convert(a.input, a.output, a.iters)
