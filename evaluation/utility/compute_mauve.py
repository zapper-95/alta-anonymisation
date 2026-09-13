import argparse
import json
import numpy as np
import mauve
from pathlib import Path


# Field names for the reference (p) and generated (q) texts
P_FIELD = "text"
Q_FIELD = "final_text"

SEEDS = [1, 2, 3]

MAUVE_KWARGS = dict(
    device_id=0,          # -1 for CPU, 0 for GPU
    max_text_length=1024,
    verbose=True,
    mauve_scaling_factor=1,
)


def main():
    parser = argparse.ArgumentParser(description="Compute MAUVE score for a JSONL file.")
    parser.add_argument("jsonl_file", type=Path, help="Path to the JSONL file to score")
    args = parser.parse_args()

    path = args.jsonl_file
    if not path.exists():
        raise SystemExit(f"[ERROR] File not found: {path}")

    # Load texts
    p_text, q_text = [], []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    item = json.loads(line)
                    p_text.append(item[P_FIELD])
                    q_text.append(item[Q_FIELD])
                except json.JSONDecodeError:
                    print(f"Skipping line: invalid JSON")
                    continue

    print(f"\n{'='*60}")
    print(f"File : {path.name}  ({len(p_text)} samples)")
    print(f"{'='*60}")

    scores = {}
    for seed in SEEDS:
        print(f"\n-- Seed {seed} --")
        out = mauve.compute_mauve(
            p_text=p_text,
            q_text=q_text,
            seed=seed,
            **MAUVE_KWARGS,
        )
        scores[seed] = out.mauve
        print(f"MAUVE score (seed={seed}): {out.mauve:.4f}")

    score_values = list(scores.values())
    mean = float(np.mean(score_values))
    std = float(np.std(score_values, ddof=1))   # sample std dev (N-1)

    print(f"\nResults for {path.name}")
    print(f"  Seed 1: {scores[1]:.4f}")
    print(f"  Seed 2: {scores[2]:.4f}")
    print(f"  Seed 3: {scores[3]:.4f}")
    print(f"  Mean:   {mean:.4f}")
    print(f"  Std:    {std:.4f}")

    # Write output JSONL alongside the input file
    out_path = path.with_name("mauve_results.jsonl")
    result_record = {
        "source_file": path.name,
        "p_field": P_FIELD,
        "q_field": Q_FIELD,
        "n_samples": len(p_text),
        "mauve_seed_1": round(scores[1], 6),
        "mauve_seed_2": round(scores[2], 6),
        "mauve_seed_3": round(scores[3], 6),
        "mean": round(mean, 6),
        "std": round(std, 6),
    }

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result_record) + "\n")

    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
