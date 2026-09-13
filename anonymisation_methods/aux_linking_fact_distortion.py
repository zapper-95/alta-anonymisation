import json
import math
import random
import copy
import threading

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import os
import tqdm

from utils.utils import enumerate_resume, write_jsonl
from generators import generator_factory, model_factory


def _pick(records, tau):
    if not records:
        return None
    above = [r for r in records if r["privacy"].get("privacy_score", 0) >= tau]
    if above:
        return max(above, key=lambda r: r["utility"].get("Utility Score", 0)
                   if isinstance(r["utility"], dict) else 0)
    # below tau: privacy first, then utility, so ties never pick a dominated candidate
    return max(records, key=lambda r: (r["privacy"].get("privacy_score", 0),
                                      r["utility"].get("Utility Score", 0)
                                      if isinstance(r["utility"], dict) else 0))


def select_best_text(original, records, tau):
    """Final selection. Returns the original text when it scores best."""
    best = _pick(records, tau)
    if best is None or best["rewriting"] is None:
        return original
    return best["rewriting"]["anonymised_text"]


def best_rewrite_so_far(records, tau):
    """Loop seeding. None means the original is still best, so reset to doc_facts."""
    best = _pick(records, tau)
    if best is None:
        return None
    return best["rewriting"]


# ---------------------------------------------------------------------------
# Fact history
# ---------------------------------------------------------------------------

def init_fact_history(doc_facts):
    return {
        i: [{"transformation": "original", "strength": "none",
             "fact": fact, "parent_iter": 0}]
        for i, fact in enumerate(doc_facts)
    }


def update_fact_history(doc_facts, cur_rewriting, fact_history, parent_iter=0):
    """Append one entry per fact per iteration, recording which iteration the
    facts were derived from so lineage can be followed later."""
    distorted = cur_rewriting["distorted_facts"]
    assigned = cur_rewriting["assigned_transformations"]
    by_id = {a.get("fact_id", pos): a for pos, a in enumerate(assigned)}

    for fact_id in range(len(doc_facts)):
        action = by_id.get(fact_id)
        if action is None:
            entry = {"transformation": "absent", "strength": "none", "fact": None}
        else:
            entry = {
                "transformation": action.get("transformation", "identity"),
                "strength": action.get("strength", "none"),
                "fact": distorted.get(fact_id),
            }
            if "n" in action:
                entry["n"] = action["n"]
        entry["parent_iter"] = parent_iter
        fact_history.setdefault(fact_id, []).append(entry)


def build_aux_info_sets(doc_facts, order, u=5):
    """Split the facts into u disjoint, non-empty subsets, one per adversary.

    `order` is a random permutation of fact indices, so the subsets are random
    while doc_facts itself stays in document order.
    """
    u = max(1, min(u, len(order)))
    q, r = divmod(len(order), u)
    subsets, start = [], 0
    for i in range(u):
        size = q + (1 if i < r else 0)
        subsets.append([doc_facts[j] for j in order[start:start + size]])
        start += size
    assert len(subsets) == u and all(subsets)
    assert sum(len(s) for s in subsets) == len(doc_facts)
    return subsets


def _seed_from(best, doc_facts):
    """Return (current_facts, current_fact_ids) for the next iteration."""
    if best is None:
        return copy.copy(doc_facts), list(range(len(doc_facts)))
    ids = sorted(best["distorted_facts"])
    return [best["distorted_facts"][k] for k in ids], ids


# ---------------------------------------------------------------------------
# Per-document loop
# ---------------------------------------------------------------------------

def _process_document(
    line, doc_idx, item,
    gen, pe_model, ue_model, act_model, parser_model,
    language, max_iters, pass_at_k, tau, u, seed, no_utility, cot
):
    item["idx"] = doc_idx
    print(item)

    parent_iter = 0
    cur_pass = 0
    complete = False
    privacy_reflections = []
    utility_reflections = []
    rewritings = []
    all_records = []           # every scored candidate, across all passes
    history_by_pass = {}       # fact_history per pass, since fact ids are per-pass
    fact_history = {}

    people = None

    if "label" in item and item['label'] == 'Medician':
        item['label'] = 'Physician'

    while cur_pass < pass_at_k and not complete:
        privacy_reflections.append(f"pass: {cur_pass}")
        utility_reflections.append(f"pass: {cur_pass}")
        rewritings.append(f"pass: {cur_pass}")

        records = []           # candidates within this pass, used for seeding

        doc_facts = json.loads(line)          # document order, never mutated
        order = list(range(len(doc_facts)))
        random.Random(f"{seed}-{doc_idx}-{cur_pass}").shuffle(order)

        fact_history = init_fact_history(doc_facts)
        current_fact_ids = list(range(len(doc_facts)))
        current_facts = copy.copy(doc_facts)

        conclusions = gen.document_conclusions(
            item["text"], doc_facts, pe_model, parser_model
        )
        print("\nDOCUMENT CONCLUSIONS:\n", conclusions, "\n")
        item["conclusions"] = conclusions


        if not doc_facts:
            raise ValueError(f"document {doc_idx} has no extracted facts; skipping")
        
        aux_info_sets = build_aux_info_sets(doc_facts, order, u=u)
        print(aux_info_sets)

        # --- evaluate the original -----------------------------------------
        privacy_evaluation = gen.privacy_aux_linking(
            pe_model, aux_info_sets, item["text"], tau, fd=True)
        print(privacy_evaluation["feedback"])
        privacy_score = privacy_evaluation["privacy_score"]
        privacy_satisfied = privacy_evaluation["privacy_satisfied"]
        privacy_feedback = privacy_evaluation["feedback"]
        privacy_reflections.append(privacy_evaluation)

        if not no_utility:
            utility_evaluation = gen.task_agnostic_utility_reflection(
                item['text'], ue_model, item["text"], conclusions)
            utility_score = utility_evaluation["Utility Score"]    # blended 0-100 utility
            utility_confirm = utility_evaluation["Confirmation"]   # "Yes"/"No" gate
            utility_feedback = utility_evaluation["Advice"]
        else:
            utility_evaluation = {'Confirmation': 'Yes', 'Advice': ''}
            utility_score = None
            utility_confirm = utility_evaluation["Confirmation"]
            utility_feedback = utility_evaluation["Advice"]
        utility_reflections.append(utility_evaluation)

        record = {"rewriting": None, "privacy": privacy_evaluation,
                  "utility": utility_evaluation}
        records.append(record)
        all_records.append(record)

        if privacy_satisfied == 'Yes' and utility_confirm == 'Yes':
            complete = True
            break

        cur_iter = 1
        complete = False
        while cur_iter <= max_iters:
            cur_rewriting = gen.rewrite(
                input_text=item["text"],
                label=None,
                people=people,
                act_model=act_model,
                parser_model=parser_model,
                cot=cot,
                strategy="aux_linking_fact_distortion",
                reflection_privacy=privacy_feedback,
                reflection_utility=utility_feedback,
                privacy_unsatisfied="No" if privacy_satisfied == "Yes" else "Yes",
                fact_history=fact_history,
                utility_score=utility_score,
                tau=tau,
                no_utility=no_utility,
                current_facts=current_facts,
                current_fact_ids=current_fact_ids,
                original_facts=doc_facts,
                conclusions=conclusions,
            )
            rewritings.append(cur_rewriting)
            print("\n")
            print(rewritings[-1]['anonymised_text'])
            print("\n")

            # update fact history with new transformations
            update_fact_history(doc_facts=doc_facts, cur_rewriting=cur_rewriting,
                                fact_history=fact_history, parent_iter=parent_iter)

            lengths = {len(h) for h in fact_history.values()}
            assert len(lengths) == 1, f"ragged fact history: {lengths}"

            # --- score this rewriting BEFORE it can become the seed --------
            text_tobe_evaluated = cur_rewriting['anonymised_text']
            privacy_evaluation = gen.privacy_aux_linking(
                pe_model, aux_info_sets, text_tobe_evaluated, tau, fd=True)
            privacy_score = privacy_evaluation["privacy_score"]
            print(f"privacy score {privacy_score}")
            privacy_satisfied = privacy_evaluation["privacy_satisfied"]
            privacy_feedback = privacy_evaluation["feedback"]
            print(privacy_feedback)
            privacy_reflections.append(privacy_evaluation)

            if not no_utility:
                utility_evaluation = gen.task_agnostic_utility_reflection(
                    item['text'], ue_model, text_tobe_evaluated, conclusions)
                
                utility_score = utility_evaluation["Utility Score"]
                utility_confirm = utility_evaluation["Confirmation"]
                utility_feedback = utility_evaluation["Advice"]
                print(f"utility_score {utility_score}")
                print(f"cosine similiarity {utility_evaluation['Cosine Similarity']}")
                print(f"conclusions support {utility_evaluation['Conclusions Support']}")
            else:
                utility_evaluation = {'Confirmation': 'Yes', 'Advice': ''}
                utility_confirm = utility_evaluation["Confirmation"]
                utility_feedback = utility_evaluation["Advice"]
            utility_reflections.append(utility_evaluation)

            record = {"rewriting": cur_rewriting, "privacy": privacy_evaluation,
                      "utility": utility_evaluation}
            records.append(record)
            all_records.append(record)

            # if solved, check if it passes the utility test, if so exit early
            if privacy_satisfied == 'Yes' and utility_confirm == 'Yes':
                print("Privacy satisfied, exiting early")
                print(f"Privacy score: {privacy_score}, Utility score: {utility_score}")
                complete = True
                break


            best = records[-1]["rewriting"]

            current_facts, current_fact_ids = _seed_from(best, doc_facts)
            parent_iter = 0 if best is None else next(
                i for i, r in enumerate(records) if r["rewriting"] is best)
            if best is not None and current_facts == doc_facts:
                print("WARNING: seed is identical to the original facts")

            cur_iter += 1
        cur_pass += 1

    item["fact_history"] = fact_history
    item["fact_history_by_pass"] = history_by_pass
    item["final_text"] = select_best_text(item['text'], all_records, tau)
    item["rewritings"] = rewritings
    item["privacy_reflections"] = privacy_reflections
    item["utility_reflections"] = utility_reflections
    item["complete"] = 'False' if not complete else 'True'
    print(f"completed document {doc_idx}")
    return item


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_aux_linking_fact_distortion(
    dataset: List[dict],
    pe_model_name: str,
    ue_model_name: str,
    act_model_name: str,
    parser_model_name: str,
    language: str,
    max_iters: int,
    pass_at_k: int,
    log_path: str,
    facts_path: str,
    tau: int,
    u:int,
    seed: int,
    no_utility: bool = False,
    cot: bool = False,
    num_workers: int = 1,
    start_idx: int = 0,
    end_idx: int = 250,
) -> None:
    gen = generator_factory(language)
    pe_model = model_factory(pe_model_name, seed)
    ue_model = model_factory(ue_model_name, seed)
    act_model = model_factory(act_model_name, seed)
    parser_model = model_factory(parser_model_name, seed)

    end_idx = len(dataset) if end_idx is None else end_idx
    subset = dataset[start_idx:end_idx]

    # ensure that each document has a fact version stored as jsonl, if not, extract the facts and store them
    gen.extract_facts_from_dataset(subset, pe_model, facts_path)

    log_lock = threading.Lock()

    # index into the fact lines rather than zipping: enumerate_resume yields only
    # the unfinished items, so zipping pairs documents with other documents' facts
    with open(facts_path, encoding="utf-8") as f:
        fact_lines = f.read().splitlines()

    tasks = [
        (fact_lines[i+start_idx], i+start_idx, item)
        for i, item in enumerate_resume(subset, log_path)
    ]

    with ThreadPoolExecutor(max_workers=num_workers) as executor, tqdm.tqdm(total=len(tasks)) as pbar:
        futures = [
            executor.submit(
                _process_document, line, i, item,
                gen, pe_model, ue_model, act_model, parser_model,
                language, max_iters, pass_at_k, tau, u, seed, no_utility, cot,
            )
            for line, i, item in tasks
        ]
        for future in as_completed(futures):
            try:
                item = future.result()
            except Exception:
                import traceback
                print(traceback.format_exc())
                pbar.update(1)
                continue
            with log_lock:
                write_jsonl(log_path, [item], append=True)
            pbar.update(1)
            act_model.print_usage()
            pe_model.print_usage()
            ue_model.print_usage()
            parser_model.print_usage()
            print(f"log path: {log_path}\n")
