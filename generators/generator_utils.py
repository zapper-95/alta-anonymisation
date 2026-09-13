import copy
import dataclasses
import os
import contextlib
import re
import string
import threading
from generators.model import ModelBase, Message
import random
import json
from sentence_transformers import SentenceTransformer
from langchain.output_parsers import ResponseSchema, StructuredOutputParser, RetryOutputParser, OutputFixingParser
from contextlib import nullcontext as _NullCtx
import numpy as np
from typing import Union, List, Optional, Callable
from utils.utils import write_jsonl

def run_generation(model, parser_model, general_system_instruction,
                   format_instructions, output_parser, response_schemas, messages,
                   temperature=1):
    """Generate; if parsing fails, run parse_fixing. Returns the output_dict."""
    output_dict = model.generate_chat(
        messages=messages,
        format_instructions=format_instructions,
        parser=output_parser,
        temperature=temperature,
    )
    if not output_dict.get('parse_success'):
        output_dict = parse_fixing(
            general_system_instruction, format_instructions, output_parser,
            output_dict, parser_model, [d.name for d in response_schemas],
        )
    return output_dict

_embedder_cache: dict = {}
_embedder_lock = threading.Lock()

def make_parser(*args):
    # Accept either (name, description) or ((name, desc), (name, desc), ...)
    if len(args) == 2 and isinstance(args[0], str):
        fields = [args]
    else:
        fields = args
    response_schemas = [ResponseSchema(name=n, description=d) for n, d in fields]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()
    return response_schemas, output_parser, format_instructions


def make_detection_parser():
    """Parser + format instructions for the CoT detection step (People + Sensitive entities)."""
    response_schemas = [
        ResponseSchema(name="People", description="name of the detected people separated by ', '"),
        ResponseSchema(
            name="Sensitive entities",
            description="the list of detected sensitive entities where every two entities are separated by ', '",
        ),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    return output_parser.get_format_instructions()


def safe_format(template, **kwargs):
    """
    format() that fails loudly when the template has no placeholder for a kwarg.

    str.format silently discards surplus keyword arguments, which meant
    fact_history was being passed to prompts that never referenced it. Used only
    for the fact-distortion prompts, whose placeholders are known; the
    reflexion/aux-linking templates deliberately omit some kwargs because
    model.generate_chat supplies format_instructions separately.
    """
    expected = {field for _, field, _, _ in string.Formatter().parse(template) if field}
    unused = set(kwargs) - expected
    if unused:
        raise KeyError(f"prompt template has no placeholder for: {sorted(unused)}")
    return template.format(**kwargs)
def _get_embedder(model_name: str = "all-mpnet-base-v2") -> SentenceTransformer:
    with _embedder_lock:
        if model_name not in _embedder_cache:
            _embedder_cache[model_name] = SentenceTransformer(model_name)
        return _embedder_cache[model_name]


def parse_fixing(general_system_instruction, format_instructions, output_parser, output_dict, parser_model, key_list):
    fixing_messages = [
        Message(
            role="system",
            content=general_system_instruction,
        ),
        Message(
            role="user",
            content=f"{format_instructions}\n\nBut I got '{output_dict['raw_response']}', help me to fix"
                    f" it to fit the given json format",
        )
    ]
    fixing_dict = parser_model.generate_chat(messages=fixing_messages,
                                             format_instructions=format_instructions,
                                             parser=output_parser)
    for k in key_list:
        output_dict[k] = copy.deepcopy(fixing_dict[k])

    return output_dict


def generic_detection(
        input_text: str,
        model: ModelBase,
        whole_task_instruction: str,
        general_task_instruction: str,
        detection_chat_instruction: str,
        detection_completion_instruction: str,
):
    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="People", description="name of the detected people separated by ', '"),
            ResponseSchema(
                name="Sensitive entities",
                description="the list of detected sensitive entities where every two entities are separated by ', '",
            ),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_task_instruction,
            ),
            Message(
                role="user",
                content=f"{whole_task_instruction}\n\n{detection_chat_instruction.format(format_instructions_1=format_instructions, input_text=input_text)}"
            )
        ]
        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                          parser=output_parser)
    else:
        prompt = f'{whole_task_instruction}\n{detection_completion_instruction}\n\n[description text]:\n{input_text}'
        output_dict, usage, finish_reason = model.generate(prompt)

    return output_dict




def generic_privacy_reflection(
        model: ModelBase,
        retriever,
        curr_rewriting: str,
        people: str,
        p_threshold: int,
        no_utility: bool,
        general_system_instruction: str,
        privacy_reflection_chat_instruction_1: str,
        privacy_reflection_completion_instruction_1: str,
        privacy_reflection_chat_instruction_2: str,
        privacy_reflection_completion_instruction_2: str
):
    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="Candidates", description=f"the sorted list of name of {p_threshold} celebrity "
                                                          "candidates where every two names are separated by \', \'")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions_1 = output_parser.get_format_instructions()

        # retrieved_docs = retriever.invoke(curr_rewriting)
        # retrieved_docs_str = ""
        # for d in retrieved_docs:
        #     retrieved_docs_str += f"{d.page_content}\n"

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{privacy_reflection_chat_instruction_1.format(format_instructions_1=format_instructions_1, p_threshold=p_threshold, curr_rewriting=curr_rewriting)}'
                        # f'The retrieved context is here:{retrieved_docs_str}',
            )
        ]
        output_dict_1 = model.generate_chat(messages=messages, format_instructions=format_instructions_1,
                                            parser=output_parser)
        candidate = output_dict_1["Candidates"].split(', ')
        emb_model = _get_embedder()
        candidate_emb = emb_model.encode(candidate)
        people_emb = emb_model.encode(people)
        sim_score = candidate_emb.dot(people_emb)
        if True in (sim_score > 0.75):
            response_schemas = [
                ResponseSchema(name="Confirmation", description="\"Yes or No\""),
                ResponseSchema(name="Advice", description="\"the list of detected sensitive entities where"
                                                          " every two entities are separated by \', \'\"}")
            ]
            output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
            format_instructions_2 = output_parser.get_format_instructions()

            messages.append(
                Message(
                    role="assistant",
                    content=output_dict_1['raw_response']
                )
            )
            messages.append(
                Message(
                    role="user",
                    content=f"{privacy_reflection_chat_instruction_2.format(people=people, format_instructions_2=format_instructions_2)}"
                )
            )
            output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions_2,
                                              parser=output_parser)
            output_dict['candidate'] = candidate
            output_dict['rank'] = int(sim_score.argmax()) + 1
            output_dict['finish_reason_1'] = output_dict_1['finish_reason']
            if 'retry_finish_reason' in output_dict_1.keys():
                output_dict['retry_finish_reason_1'] = output_dict_1['retry_finish_reason']
        else:
            output_dict = output_dict_1
            output_dict["Confirmation"] = "No"
            output_dict["Advice"] = ""
            output_dict['candidate'] = candidate
            output_dict['rank'] = sim_score.size + 1
    else:
        output_dict = model.generate(
            f'{privacy_reflection_completion_instruction_1}\n[Description text]:\n{curr_rewriting}\n[Person name]:\n{people}')

    return output_dict  # type: ignore

def task_agnostic_utility_reflection(
        input_text: str,
        model: ModelBase,
        curr_rewriting: str,
        general_system_instruction: str,
        utility_reflection_chat_instruction_1: str,
        utility_reflection_completion_instruction_1: str,
        conclusions: str
):
    # --- cosine similarity: semantic fidelity to the original ---
    embedder = _get_embedder()
    emb_in, emb_out = embedder.encode([input_text, curr_rewriting])
    cos = float(np.dot(emb_in, emb_out) /
                (np.linalg.norm(emb_in) * np.linalg.norm(emb_out)))
    cos = max(0.0, min(1.0, cos))

    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="Supports Conclusions",
                           description="integer 0-10: how far does the text support the following conclusions and inferences"),
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(role="system", content=general_system_instruction),
            Message(
                role="user",
                content=f'{utility_reflection_chat_instruction_1.format(format_instructions=format_instructions, curr_rewriting=curr_rewriting, conclusions=conclusions)}',
            ),
        ]
        output_dict = model.generate_chat(messages=messages,
                                          format_instructions=format_instructions,
                                          parser=output_parser,
                                        temperature=0
                                          )

        def _score(key):
            try:
                return max(0, min(10, int(output_dict.get(key, 5))))
            except (TypeError, ValueError):
                return 5

        conclusions_support =  _score("Supports Conclusions")
        utility_score = (0.9*(conclusions_support/10) + 0.1 * (cos)) * 100



        output_dict["Utility Score"] = round(utility_score)  # keep 0-100 scale for the loop
        output_dict["Cosine Similarity"] = cos
        output_dict["Conclusions Support"] = conclusions_support
        output_dict["Confirmation"] = "Yes" if utility_score >= 95 else "No"
        output_dict["Advice"] = ""
    else:
        output_dict = model.generate(
            f'{utility_reflection_completion_instruction_1}\n[Original text]:\n{input_text}\n[anonymised_text]:\n{curr_rewriting}'
        )

    return output_dict  # type: ignore



def generic_utility_reflection(
        input_text: str,
        model: ModelBase,
        label: str,
        privacy_score: str,
        curr_rewriting: str,
        general_system_instruction: str,
        utility_reflection_chat_instruction_1: str,
        utility_reflection_completion_instruction_1: str,
):
    if model.is_chat:
        response_schemas = [
            # ResponseSchema(name="Occupation", description="the occupation you choose"),
            ResponseSchema(name="Confidence Score", description="the confidence score of making the classification")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{utility_reflection_chat_instruction_1.format(format_instructions=format_instructions, curr_rewriting=curr_rewriting, label=label)}',
            )
        ]
        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                          parser=output_parser)
        # occupation = output_dict['Occupation']
        confidence_score = int(output_dict["Confidence Score"])
        if confidence_score <= 95:
            output_dict["Confirmation"] = "No"
        else:
            output_dict["Confirmation"] = "Yes"
        output_dict["Advice"] = ""
    else:
        output_dict = model.generate(
            f'{utility_reflection_completion_instruction_1}\n[Original text]:\n{input_text}\n[anonymised_text]:\n{curr_rewriting}\n[Classification label]{label}')

    return output_dict  # type: ignore


def generic_privacy_confidence_evaluation(
        model: ModelBase,
        curr_rewriting: str,
        people: str,
        general_system_instruction: str,
        privacy_confidence_evaluation_instruction: str,
):
    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="Confidence Score", description="the confidence score of making your choice"),
            ResponseSchema(name="Reason", description="the reason for your scoring")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{privacy_confidence_evaluation_instruction.format(format_instructions=format_instructions, curr_rewriting=curr_rewriting, people=people)}',
            )
        ]
        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                          parser=output_parser, temperature=0)
    else:
        output_dict = model.generate(
            f'{privacy_confidence_evaluation_instruction}\n[Description text]:\n{curr_rewriting}\n[Person name]:\n{people}')

    return output_dict  # type: ignore


def generic_privacy_selection_evaluation(
        model: ModelBase,
        curr_rewriting: str,
        original_text: str,
        people: str,
        candidate_list: str,
        general_system_instruction: str,
        candidate_generation_instruction: str,
        privacy_selection_evaluation_instruction: str,
):
    if model.is_chat:
        gn_flag = False
        if candidate_list is None:
            gn_flag = True
            response_schemas = [
                ResponseSchema(name="Similar celebrities", description="the list of the most similar celebrities where "
                                                                       "every two celebrities are separated by a comma")
            ]
            output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
            format_instructions = output_parser.get_format_instructions()

            messages = [
                Message(
                    role="system",
                    content=general_system_instruction,
                ),
                Message(
                    role="user",
                    content=f'{candidate_generation_instruction.format(format_instructions=format_instructions, curr_rewriting=curr_rewriting, people=people)}',
                )
            ]

            output_dict_1 = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                                parser=output_parser, temperature=0)
            candidate_list = copy.deepcopy(output_dict_1["Similar celebrities"])
            candidate_list = candidate_list.split(', ')
            candidate_list.append(people)
            random.shuffle(candidate_list)
            candidate_list = ', '.join(candidate_list)
        response_schemas = [
            ResponseSchema(name="People", description="the name of the most possible celebrity")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{privacy_selection_evaluation_instruction.format(format_instructions=format_instructions, curr_rewriting=curr_rewriting, candidate_list=candidate_list)}',
            )
        ]
        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                          parser=output_parser)
        emb_model = _get_embedder()
        candidate_emb = emb_model.encode(output_dict['People'])
        people_emb = emb_model.encode(people)
        sim_score = candidate_emb.dot(people_emb)
        if sim_score > 0.75:
            output_dict['success'] = True
        else:
            output_dict['success'] = False
        if gn_flag:
            output_dict['candidate_list'] = candidate_list
            output_dict['finish_reason_1'] = output_dict_1['finish_reason']
            if 'retry_finish_reason' in output_dict_1.keys():
                output_dict['retry_finish_reason_1'] = output_dict_1['retry_finish_reason']
    else:
        output_dict = model.generate(
            f'{privacy_selection_evaluation_instruction}\n[Description text]:\n{curr_rewriting}\n[Person name]:\n{people}')

    return output_dict  # type: ignore


def qa_evaluation(
        model: ModelBase,
        anonymised_text,
        question,
        choices,
        answer_indx,
        general_system_instruction,
        qa_instruction
):
    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="Answer Index", description="The 0 based index of your selected answer from the list of options")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{qa_instruction.format(format_instructions=format_instructions, outline=anonymised_text, question=question, choices=choices)}',
            )
        ]

        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                            parser=output_parser, temperature=0)
        guessed_answer = copy.deepcopy(output_dict["Answer Index"])
        output_dict["guess"] = guessed_answer
        if guessed_answer.isdigit() and int(guessed_answer) == answer_indx:
            output_dict['success'] = True
        else:
            output_dict['success'] = False

    else:
        raise NotImplementedError("qa_evaluation is only implemented for chat models")

    return output_dict  # type: ignore



def med_privacy_confidence_evaluation(
        model: ModelBase,
        anonymised_text: str,
        question: str,
        answer:str,
        general_system_instruction: str,
        privacy_confidence_evaluation_instruction: str,
):
    if model.is_chat:
        response_schemas = [
            ResponseSchema(name="Confidence Score", description="the confidence score of making your choice"),
            ResponseSchema(name="Reason", description="the reason for your scoring")
        ]
        output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = output_parser.get_format_instructions()

        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=f'{privacy_confidence_evaluation_instruction.format(format_instructions=format_instructions, anonymised_text=anonymised_text,question=question, answer=answer)}',
            )
        ]
        output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions,
                                          parser=output_parser, temperature=0)
    else:
        output_dict = model.generate(
            f'{privacy_confidence_evaluation_instruction}\n[Description text]:\n{anonymised_text}\n[Answer]:\n{answer}', temperature=0)

    return output_dict  # type: ignore


def sample_n_random(items: List[str], n: int) -> List[str]:
    """Sample min(n, len(items)) random items from a list"""
    assert n >= 0
    if n >= len(items):
        return items
    return random.sample(items, n)

def print_messages(system_message_text: str, user_message_text: str) -> None:
    print(f"""----------------------- SYSTEM MESSAGE -----------------------)
{system_message_text}
----------------------------------------------
----------------------- USER MESSAGE -----------------------
{user_message_text}
----------------------------------------------
""", flush=True)

def print_generated_func_body(func_body_str: str) -> None:
    print(f"""--------------------- GENERATED FUNC BODY ---------------------
{func_body_str}
------------------------------------------""")
    


import concurrent.futures


def generic_privacy_aux_linking(model, aux_info_sets, curr_rewriting, tau, general_system_instruction, aux_confidence_instruction, feedback_synthesis_instruction, max_workers=5):

    if not model.is_chat:
        raise NotImplementedError("privacy linkage only support GPT currently")

    response_schemas = [
        ResponseSchema(name="feedback", description="the reason for your scoring"),
        ResponseSchema(name="aux_confidence", description="the confidence score of auxilliary information linking to this text"),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions = output_parser.get_format_instructions()

    def _score_one(aux_info):
        messages = [
            Message(
                role="system",
                content=general_system_instruction,
            ),
            Message(
                role="user",
                content=aux_confidence_instruction.format(
                    format_instructions=format_instructions,
                    prev_rewriting=curr_rewriting,
                    aux_info=aux_info,
                ),
            ),
        ]
        return model.generate_chat(
            messages=messages,
            format_instructions=format_instructions,
            parser=output_parser,
            temperature=0,
        )

    # Score all subsets concurrently, preserve input order, isolate failures
    subset_outputs = [None] * len(aux_info_sets)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(_score_one, aux): i
            for i, aux in enumerate(aux_info_sets)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                subset_outputs[idx] = future.result()
            except Exception as e:
                subset_outputs[idx] = {"parse_success": False, "error": str(e)}

    # Collect successfully-parsed (confidence, feedback, aux_info) triples
    parsed = []
    for aux_info, out in zip(aux_info_sets, subset_outputs):
        if not out.get("parse_success"):
            continue
        if "aux_confidence" not in out or "feedback" not in out:
            continue
        try:
            confidence = int(out["aux_confidence"])
        except (TypeError, ValueError):
            continue
        parsed.append({
            "aux_info": aux_info,
            "confidence": confidence,
            "feedback": out["feedback"],
        })

    if not parsed:
        return {
            "parse_success": False,
            "subset_outputs": subset_outputs,
            "privacy_score": 0,
            "privacy_satisfied": "No",
            "feedback": "All subset evaluations failed to parse.",
        }

    # Aggregate confidence: worst-case (max) is the GDPR-aligned summary
    confidences = [p["confidence"] for p in parsed]
    
    # worst case privacy scenario, weighted 80:20 max vs mean. Allows finer granularity when same highest confidence for two texts
    aggregate_confidence = int(0.8*(max(confidences)) + 0.2 * (sum(confidences)/len(confidences)))
    privacy_score = 100 - aggregate_confidence
    # Synthesise per-subset feedback into a single directive for the rewriter
    per_subset_block = "\n\n".join(
        f"Subset {i+1} (confidence={p['confidence']}):\n"
        f"  Auxiliary information: {p['aux_info']}\n"
        f"  Reasoning: {p['feedback']}"
        for i, p in enumerate(parsed)
    )
    #print(per_subset_block)
    synthesis_messages = [
            Message(
                role="user",
                content=feedback_synthesis_instruction.format(
                    current_text=curr_rewriting,
                    per_subset_feedback=per_subset_block,
                ),
            ),
        ]
    synthesis_text = model.generate_chat_plain(
        messages=synthesis_messages,
        temperature=0,
    )

    output_dict = {
        "parse_success": True,
        "subset_outputs": subset_outputs,
        "aux_confidence": aggregate_confidence,
        "mean_confidence": sum(confidences) / len(confidences),
        "n_subsets_scored": len(parsed),
        "n_subsets_total": len(aux_info_sets),
        "privacy_score": privacy_score,
        "privacy_satisfied": "Yes" if privacy_score >= tau else "No",
        "feedback": synthesis_text,
    }

    return output_dict


 
def _scrub_name(facts: List[str], name: str, replacement: str = "the person") -> List[str]:
    """Replace the person's full name with `replacement` in every fact. Case-insensitive, whole-word."""
    if not name:
        return facts
    return [re.sub(rf"\b{re.escape(name)}\b", replacement, f, flags=re.IGNORECASE) for f in facts]
 
 
def extract_facts_from_dataset(dataset: List[dict], model: ModelBase, log_path: str, general_system_instruction: str, fact_extraction_instruction_1: str) -> None:
    """Extract facts from the dataset and store them in a jsonl file"""
    if not os.path.exists(log_path):
        for i, doc in enumerate(dataset):
            text = doc['text']
            facts = extract_facts_from_text(text, model, general_system_instruction, fact_extraction_instruction_1)
            write_jsonl(log_path, [facts], append=True)
    else:
        print("Reusing existing facts")


def extract_facts_from_text(text: str, model: ModelBase, general_system_instruction: str, fact_extraction_instruction_1: str) -> List[str]:
    """Extract a flat list of facts from a single document."""
    if not model.is_chat:
        raise NotImplementedError("extract_facts_from_text only supports chat models")

    response_schemas = [
        ResponseSchema(
            name="Facts",
            description="a JSON array of strings, where each string is one atomic fact extracted from the text, "
                        "e.g. [\"the person was born in 1942\", \"the person is a photographer\"]"
        ),
    ]
    output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
    format_instructions_1 = output_parser.get_format_instructions()

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(
            role="user",
            content=fact_extraction_instruction_1.format(
                format_instructions=format_instructions_1, input_text=text
            ),
        ),
    ]
    output_dict_1 = model.generate_chat(
        messages=messages, format_instructions=format_instructions_1, parser=output_parser,temperature=0
    )

    facts = output_dict_1["Facts"]
    if isinstance(facts, str):
        facts = json.loads(facts)
    return [str(fact) for fact in facts]

def document_conclusions(input_text, facts, model, parser_model,
                         general_system_instruction,
                         document_conclusions_instruction):
    """
    Establish, once, what the original document conveys.

    Computed from the original text before any transformation and held fixed for
    the whole run. Derived per-iteration from the current facts instead, the
    conclusions drift with the distortions and the loop ends up preserving
    whatever the anonymised document now says rather than what the original said.
    """

    labelled_facts = "\n".join(f"{f}" for _, f in enumerate(facts))

    response_schemas, output_parser, format_instructions = make_parser(
        ("summary", "a single sentence summarising what the document is about, containing "
                    "no proper nouns and no specific values"),
        ("inferences", "the inferences a reader should be able to draw, each stated as a "
                       "claim about what is the case, containing no proper nouns and no "
                       "specific values"),
        # ("facts", "at most 3 facts that support each inference, with the facts listed verbatim in a list of lists"),
        )

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(
            role="user",
            content=safe_format(
                document_conclusions_instruction,
                format_instructions=format_instructions,
                input_text=input_text,
                facts=labelled_facts
            ),
        ),
    ]

    output_dict = run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages, temperature=1,
    )

    parts = []
    if output_dict.get("summary"):
        parts.append(f"What the document is about:\n{output_dict['summary']}")
    if output_dict.get("inferences"):
        parts.append(f"Inferences a reader should be able to draw:\n{output_dict['inferences']}")
    # if output_dict.get("facts"):
    #     parts.append(f"Supporting facts:\n{output_dict['facts']}")
    return "\n\n".join(parts) if parts else "no conclusions established"