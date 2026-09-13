import json
import string

from generators.model import ModelBase, Message
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from generators.generator_utils import parse_fixing
from generators.generator_utils import safe_format, make_parser, make_detection_parser, run_generation
from rewriters.fact_helpers import _fact_string, _facts_to_numbered_block, _facts_with_lineage_block, _format_lineage, _is_deleted, _lineage_values, _parse_distorted_fact_list, _parse_transformation_list, _parse_utility_transformation_list, _walk_back


VALID_TRANSFORMATIONS = {"coarsen", "perturb", "specialise", "delete", "identity"}
VALID_STRENGTHS = {"low", "medium", "high", "none"}
VALID_UTILITY_TRANSFORMATIONS = {"undo", "restore", "identity"}

class aux_linking_rewrite_fact_distortion():
    """
    Fact-distortion driver. Delegates to the privacy-mode or utility-mode pipeline
    based on `privacy_unsatisfied`.

    Extra parameters not used by this driver are accepted for caller compatibility
    with the reflexion/aux_linking drivers (which share a dispatcher).
    """

    @staticmethod
    def rewrite(
        input_text: str,
        model: ModelBase,
        parser_model: ModelBase,
        reflection_privacy,
        general_system_instruction: str,
        fact_transformation_instruction: str,
        fact_rewriting_instruction: str,
        document_rewriting_instruction: str,
        current_facts,
        original_facts,
        current_fact_ids,
        fact_history: dict = None,
        fact_transformation_utility_instruction: str = None,
        privacy_unsatisfied: str = 'Yes',
        conclusions: str = None,
    ):
        if privacy_unsatisfied == 'Yes' or fact_transformation_utility_instruction is None:
            return run_fact_distortion_rewrite(
                input_text, original_facts, current_facts, current_fact_ids,
                fact_history,
                reflection_privacy, model, parser_model,
                general_system_instruction,
                fact_transformation_instruction,
                fact_rewriting_instruction,
                document_rewriting_instruction,
                conclusions,
            )
        return run_utility_fact_distortion_rewrite(
            input_text, original_facts, current_facts, current_fact_ids, fact_history,
            reflection_privacy, model, parser_model,
            general_system_instruction,
            fact_transformation_utility_instruction,
            document_rewriting_instruction,
            conclusions,    
        )


def run_fact_distortion_rewrite(input_text, original_facts, current_facts, current_fact_ids,
                                fact_history,
                                reflection_privacy, model, parser_model,
                                general_system_instruction,
                                fact_transformation_instruction,
                                fact_rewriting_instruction,
                                document_rewriting_instruction,
                                conclusions,
                                ):
    """
    Privacy-mode three-stage pipeline: assign transformations, apply them to
    produce distorted facts, then rewrite the document. Distorted-fact strings
    are attached to the returned output_dict under 'distorted_facts'.
    """
    assigned = fact_distortion_assign_transformations(
        original_facts=original_facts,
        current_facts=current_facts,
        current_fact_ids=current_fact_ids,
        fact_history=fact_history,
        reflection_privacy=reflection_privacy,
        model=model,
        parser_model=parser_model,
        general_system_instruction=general_system_instruction,
        fact_transformation_instruction=fact_transformation_instruction,
        conclusions=conclusions
    )
    distorted_facts = fact_distortion_apply_transformations(
            assigned=assigned,
            fact_history=fact_history,
            model=model,
            parser_model=parser_model,
            general_system_instruction=general_system_instruction,
            fact_rewriting_instruction=fact_rewriting_instruction,
            reflection_privacy=reflection_privacy,
            conclusions=conclusions
        )
    output_dict = fact_distortion_rewrite_document(
            distorted_facts=distorted_facts,
            original_text=input_text,
            model=model,
            parser_model=parser_model,
            general_system_instruction=general_system_instruction,
            document_rewriting_instruction=document_rewriting_instruction,
    )
    output_dict["distorted_facts"] = distorted_facts
    output_dict["assigned_transformations"] = assigned
    return output_dict

def run_utility_fact_distortion_rewrite(input_text, original_facts, current_facts,
                                        current_fact_ids, fact_history,
                                        reflection_privacy, model, parser_model,
                                        general_system_instruction,
                                        fact_transformation_utility_instruction,
                                        document_rewriting_instruction, conclusions):
    """
    Utility-mode three-stage pipeline: choose undo, restore or identity, apply them, then rewrite.
    """
    assigned = fact_distortion_assign_utility_transformations(
        original_facts, current_facts, current_fact_ids, fact_history, reflection_privacy,
        model, parser_model, general_system_instruction,
        fact_transformation_utility_instruction,conclusions
    )
    restored_facts = fact_distortion_apply_utility_transformations(
        assigned, original_facts, fact_history
    )
    print(f"Restored facts: {restored_facts}")
    output_dict = fact_distortion_rewrite_document(
        restored_facts, input_text, model, parser_model,
        general_system_instruction, document_rewriting_instruction,
    )
    output_dict["distorted_facts"] = restored_facts
    output_dict["assigned_transformations"] = assigned
    return output_dict



def fact_distortion_assign_transformations(original_facts, current_facts, current_fact_ids,
                                           fact_history, reflection_privacy, model, parser_model,
                                           general_system_instruction,
                                           fact_transformation_instruction, conclusions):
    """
    Stage 1 (privacy mode). Ask the model to choose a transformation for each fact
    in current_facts. Facts with an unrecognised/missing transformation default to
    identity. Returns [{"fact_id", "fact", "transformation", "strength"}, ...]
    aligned to current_facts.
    """
    response_schemas, output_parser, format_instructions = make_parser(
        ("reasoning", "6-7 lines of reasoning about which information requires "
                    "transformation and how strongly, considering the utility trade off and consistency across facts"),
        ("transformations", "a JSON array with one object per fact in the same order, each "
                            "of the form {\"fact\": <the fact text>, \"transformation\": "
                            "<one of coarsen, perturb, specialise, delete, identity>, "
                            "\"strength\": <one of low, medium, high; use \"none\" for "
                            "delete and identity>}"),
    )

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(
            role="user",
            content=fact_transformation_instruction.format(
                format_instructions=format_instructions,
                original_facts=_facts_to_numbered_block(original_facts),
                current_facts=_facts_with_lineage_block(
                    current_facts, current_fact_ids, fact_history),
                reflection_privacy=reflection_privacy,
                conclusions=conclusions,
            ),
        ),
    ]

    output_dict = run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages, temperature=0,
    )
    print()
    print(output_dict.get("reasoning", ""))
    print()
    print(output_dict.get("transformations", ""))
    print()

    return _parse_transformation_list(
        output_dict.get("transformations", []), current_facts, current_fact_ids,
        VALID_TRANSFORMATIONS, VALID_STRENGTHS,
    )

def fact_distortion_apply_transformations(assigned, fact_history, model, parser_model,
                                          general_system_instruction,
                                          fact_rewriting_instruction, reflection_privacy, conclusions):
    to_rewrite = [
        (i, a) for i, a in enumerate(assigned)
        if a["transformation"] not in ("identity", "delete")
    ]

    rewritten_by_index = {}
    if to_rewrite:
        response_schemas, output_parser, format_instructions = make_parser(
            ("reasoning", "3-5 sentences planning the choices that must stay consistent "
                          "across facts: recurring entities and the single perturbed "
                          "value each will take, date and age arithmetic, and real "
                          "replacements for public entities"),
            ("distorted_facts", "a JSON array of strings, one distorted fact per input "
                                "fact in the same order"),
        )

        lines = []
        for k, (_, a) in enumerate(to_rewrite):
            lines.append(
                f"{k + 1}. fact: {a['fact']} | transformation: {a['transformation']} | "
                f"strength: {a.get('strength', 'none')}"
            )
            history = fact_history.get(a["fact_id"]) if fact_history else None
            if history and len(history) > 1:
                previous = _lineage_values(history)[:-1]
                if previous:
                    lines.append(f"   already used: {_format_lineage(previous)}")
        block = "\n".join(lines)

        unchanged = [a["fact"] for a in assigned if a["transformation"] == "identity"]
        unchanged_block = "\n".join(f"- {f}" for f in unchanged) or "none"

        messages = [
            Message(role="system", content=general_system_instruction),
            Message(
                role="user",
                content=fact_rewriting_instruction.format(
                    format_instructions=format_instructions,
                    fact_transformations=block,
                    unchanged_facts=unchanged_block,
                    reflection_privacy=reflection_privacy,
                    conclusions=conclusions,
                ),
            ),
        ]
        output_dict = run_generation(
            model, parser_model, general_system_instruction,
            format_instructions, output_parser, response_schemas, messages, temperature=1,
        )
        print()
        print(output_dict.get("reasoning", ""))
        print()
        distorted = _parse_distorted_fact_list(output_dict.get("distorted_facts", []))
        if len(distorted) != len(to_rewrite):
            # length mismatch — fall back to the original fact for any missing slot
            distorted = list(distorted) + [None] * (len(to_rewrite) - len(distorted))

        for (idx_in_assigned, a), new_fact in zip(to_rewrite, distorted):
            rewritten_by_index[idx_in_assigned] = new_fact or a["fact"]
            print(f"  [{a['fact_id']}] {a['transformation']}/{a.get('strength', 'none')}: "
                  f"{a['fact']}  ->  {new_fact}")

    result = {}
    for i, a in enumerate(assigned):
        if a["transformation"] == "delete":
            continue
        # identity, or the model failed to rewrite this one, falls back to a["fact"]
        result[a["fact_id"]] = rewritten_by_index.get(i, a["fact"])
    return result



def fact_distortion_assign_utility_transformations(original_facts, current_facts,
                                                   current_fact_ids,
                                                   fact_history, reflection_privacy,
                                                   model, parser_model,
                                                   general_system_instruction,
                                                   fact_transformation_utility_instruction, conclusions):
    """
    Stage 1 (utility mode). Ask the LLM to choose an inverse transformation
    for each fact in the *original* fact list. Returns a list of
    {"fact_id", "transformation", "n"} dicts, one per original fact,
    in original-fact order. Facts with no valid response default to identity.
    """
    response_schemas, output_parser, format_instructions = make_parser(
        "Transformations",
        "a JSON array with one object per original fact, each of the form "
        "{\"fact_id\": <the zero-based integer id of the original fact, exactly as "
        "numbered in the list below>, "
        "\"transformation\": <one of undo, restore, identity>, "
        "\"n\": <positive integer, required when transformation is undo, "
        "otherwise ignored>}",
    )
    messages = [
        Message(role="system", content=general_system_instruction),
        Message(
            role="user",
            content=safe_format(
                fact_transformation_utility_instruction,
                format_instructions=format_instructions,
                original_facts=_facts_to_numbered_block(original_facts),
                current_facts=_facts_to_numbered_block(current_facts, current_fact_ids),
                reflection_privacy=reflection_privacy,
                fact_history=fact_history,
                conclusions=conclusions,
            ),
        ),
    ]
    output_dict = run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages, temperature=0,
    )
    return _parse_utility_transformation_list(
        output_dict.get("Transformations", []), original_facts, VALID_UTILITY_TRANSFORMATIONS,
    )


def fact_distortion_apply_utility_transformations(assigned, original_facts, fact_history):
    """
    Utility-mode application. Purely programmatic — no LLM call.

    History carries exactly one entry per fact per iteration, with index 0 the
    original state, so undo(n) is a walk back n entries.

    Args:
        assigned: list of {"fact_id", "transformation", "n"} dicts.
        original_facts: list of original fact strings, indexed by fact_id.
        fact_history: dict mapping fact_id -> list of
            {"transformation", "strength", "fact"} entries, where fact is None
            when the fact was not present at that iteration.

    Returns:
        Dict mapping fact_id -> fact string for facts present in the resulting
        document. Facts that resolve to a deleted state are omitted.
    """
    result = {}

    for action in assigned:
        fact_id = action["fact_id"]
        transformation = action.get("transformation", "identity")
        if transformation not in VALID_UTILITY_TRANSFORMATIONS:
            transformation = "identity"

        original = original_facts[fact_id] if fact_id < len(original_facts) else ""
        history = fact_history.get(fact_id, [])
        current = history[-1] if history else None

        if transformation == "identity":
            # keep the current state, including an absence
            if not _is_deleted(current):
                result[fact_id] = _fact_string(current)
            continue

        if transformation == "restore":
            if original:
                result[fact_id] = original
            continue

        # undo(n): step back n generations along the parent chain
        try:
            n = max(1, int(action.get("n", 1)))
        except (TypeError, ValueError):
            n = 1

        target_idx = _walk_back(history, n)
        target = history[target_idx] if history else None
        if target is None or _is_deleted(target):
            if original:
                result[fact_id] = original
        else:
            result[fact_id] = _fact_string(target)

    return result


def fact_distortion_rewrite_document(distorted_facts, original_text, model, parser_model,
                                     general_system_instruction,
                                     document_rewriting_instruction):
    """
    Stage 3 (shared). Rewrite the anonymised text from the distorted fact set.
    original_text is provided as a structural/style scaffold only; the facts are
    authoritative.
    """
    response_schemas, output_parser, format_instructions = make_parser(
        "anonymised_text", "your anonymization result",
    )
    # sort by fact_id so the fact order does not depend on insertion order,
    # which differs between privacy and utility mode
    distorted_block = "\n".join(
        f"- {distorted_facts[fid]}" for fid in sorted(distorted_facts)
    )
    messages = [
        Message(role="system", content=general_system_instruction),
        Message(
            role="user",
            content=document_rewriting_instruction.format(
                format_instructions=format_instructions,
                distorted_facts=distorted_block,
                style_reference=original_text,
            ),
        ),
    ]
    return run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages, temperature=1,
    )