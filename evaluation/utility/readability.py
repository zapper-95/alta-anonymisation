"""
Score reference-free readability of anonymised documents using GPT-5.

Reads a JSONL file where each line has an "anonymised_text" field, calls the
model once per document, and writes results (score + reasoning) to a new JSONL
file. Prints the mean score at the end.

Usage:
    # requires OPENAI_KEY in environment or in a .env file at CWD
    python readability.py input.jsonl output.jsonl
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


import argparse
import json
import os

from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from pydantic import BaseModel, Field
from tqdm import tqdm
from generators.model import GPT5, Message


SYSTEM_PROMPT = (
"You are judging the readability of a document. Rate on the following scale "
    "how readable and natural the text is. Do not judge the truth of any facts, "
    "only how the text reads.\n\n"
    "1 - Unreadable: severely broken grammar, incoherent sentences, or nonsensical structure.\n"
    "2 - Poor: frequently awkward phrasing, unnatural word choices, or jarring transitions that disrupt reading.\n"
    "3 - Adequate: understandable throughout but noticeably stilted, repetitive, or formulaic in places.\n"
    "4 - Good: reads naturally with only minor awkwardness that would not distract a typical reader.\n"
    "5 - Excellent: reads like a well-written, naturally authored document with no noticeable issues.\n\n"
    "Give one or two sentences of reasoning, then the score."
)


class ReadabilityScore(BaseModel):
    reasoning: str = Field(description="One or two sentences of reasoning.")
    score: int = Field(ge=1, le=5, description="Readability score, 1 to 5.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_jsonl", type=Path)
    ap.add_argument("output_jsonl", type=Path)
    ap.add_argument("--model_name", default="gpt-5.4-mini")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--text-field",
                    help="JSON field holding the text to score.")
    ap.add_argument("--limit", type=int, default=None,
                    help="Optional cap on number of lines to process.")
    args = ap.parse_args()

    load_dotenv()  # reads .env from CWD if present

    api_key = os.environ.get("OPENAI_KEY")
    if not api_key:
        sys.exit("OPENAI_KEY not set (checked environment and .env).")

    model = GPT5(name=args.model_name, seed=args.seed)

    with args.input_jsonl.open(encoding="utf-8") as f:
        lines = [ln for ln in f if ln.strip()]
    if args.limit:
        lines = lines[: args.limit]

    # Parser is identical for every document, so build it once outside the loop.
    response_schemas = [
        ResponseSchema(name="Reasoning", description="Reasoning of the readibility score"),
        ResponseSchema(
            name="Score",
            description="Score judging readbility from 1-5, provide ONLY a single integer here, with your score and nothing else",
        ),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    scores: list[int] = []
    with args.output_jsonl.open("w", encoding="utf-8") as out:
        for i, line in enumerate(tqdm(lines, desc="scoring")):
            record = json.loads(line)
            text = record.get(args.text_field)
            if not isinstance(text, str) or not text.strip():
                out.write(json.dumps({"idx": i, "error": "missing text"}) + "\n")
                out.flush()
                continue

            messages = [
                Message(role="system", content=SYSTEM_PROMPT),
                Message(role="user", content=f"Document:\n{text}"),
            ]
            output_dict = model.generate_chat(
                messages=messages,
                format_instructions=format_instructions,
                parser=output_parser,
                temperature=0,
            )

            # Validate the score: must be parseable as an int in [1, 10].
            try:
                score = int(output_dict.get("Score"))
                if not 1 <= score <= 10:
                    raise ValueError
            except (TypeError, ValueError):
                print("Score failed")
                score = 0

            if score:  # only count valid scores toward the mean
                scores.append(score)
            out.write(json.dumps({
                "idx": i,
                "score": score,
                "reasoning": output_dict.get("Reasoning", ""),
            }) + "\n")
            out.flush()  # so the file can be tailed while the run is in progress

        # Still inside the `with` block: the file is open, so this write works.
        if scores:
            mean = sum(scores) / len(scores)
            print(f"\nmean score: {mean:.2f}  (n={len(scores)})")
            out.write(json.dumps({"mean_score": mean, "n": len(scores)}) + "\n")
        else:
            print("no successful scores.")


if __name__ == "__main__":
    main()