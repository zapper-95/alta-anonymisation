from generators.model import ModelBase
from rewriters.aux_linking_fact_distortion_rewrite import aux_linking_rewrite_fact_distortion
from rewriters.aux_linking_rewrite import aux_linking_rewrite
from rewriters.reflexion_rewrite import reflexion_rewrite
from rewriters.simple_rewrite import simple_rewrite
from .generator_types import Generator
from .generator_utils import (document_conclusions,extract_facts_from_dataset, generic_detection, generic_privacy_aux_linking,
                              generic_privacy_reflection, generic_utility_reflection,task_agnostic_utility_reflection,
                              generic_privacy_selection_evaluation, generic_privacy_confidence_evaluation, qa_evaluation)

from typing import Optional, List, Union
import ast
import re
import os
from prompts.people_prompt import *
from prompts.prompt import  REFELECTION_PRIVACY_REWRITING_INSTRUCTION
from prompts.agnostic_prompt import *
class ReWriter(Generator):




    def detect(self, input_text: str, model: ModelBase):
        return generic_detection(
            input_text=input_text,
            model=model,
            whole_task_instruction=WHOLE_TASK_INSTRUCTION,
            general_task_instruction=GENERAL_SYSTEM_INSTRUCTION,
            detection_chat_instruction=DETECTION_INSTRUCTION,
            detection_completion_instruction=DETECTION_INSTRUCTION,
        )

    def rewrite(
            self,
            input_text: str,
            label: str,
            people,
            act_model: ModelBase,
            parser_model: ModelBase,
            strategy: str,
            cot: bool = False,
            prev_rewriting: Optional[str] = None,
            reflection_privacy: Optional[str] = None,
            reflection_utility: Optional[str] = None,
            privacy_unsatisfied: Optional[int] = None,
            fact_history: Optional[dict[str, list[str]]] = None,
            utility_score: Optional[int] = None,
            detection_result: Optional[str] = None,
            num_comps: int = 1,
            temperature: float = 0.0,
            p_threshold: int = 10,
            tau: int = 80,
            no_utility: bool = False,
            current_facts=None,
            original_facts=None,
            current_fact_ids=None,
            conclusions: Optional[str] = None
    ):
        if strategy == "simple":
            return simple_rewrite().rewrite(
            input_text=input_text,
            model=act_model,
            parser_model=parser_model,
            cot=cot,
            detection_result=detection_result,

            whole_task_instruction=WHOLE_TASK_INSTRUCTION,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            detection_result_prefix=DETECTION_INSTRUCTION,
            simple_rewriting_instruction= SIMPLE_REWRITING_INSTRUCTION,
            simple_rewriting_instruction_cot=SIMPLE_REWRITING_INSTRUCTION_COT
        )
        elif strategy == "reflexion":
            return reflexion_rewrite().rewrite(
                input_text=input_text,
                label=label,
                people=people,
                model=act_model,
                parser_model=parser_model,
                prev_rewriting=prev_rewriting,
                reflection_privacy=reflection_privacy,
                privacy_unsatisfied=privacy_unsatisfied,
                utility_score=utility_score,
                general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
                reinforcement_learning_instruction=REINFORCEMENT_INSTRUCTION,
                language='wiki',
                p_threshold=p_threshold,
                cot=cot,
                detection_result=detection_result,
                no_utility=no_utility,
                whole_task_instruction=WHOLE_TASK_INSTRUCTION,
                detection_result_prefix=DETECTION_INSTRUCTION,
                simple_rewriting_instruction=SIMPLE_REWRITING_INSTRUCTION,
                simple_rewriting_instruction_cot=SIMPLE_REWRITING_INSTRUCTION_COT,
                reflection_privacy_rewriting_instruction=REFELECTION_PRIVACY_REWRITING_INSTRUCTION,
            )
        elif strategy == "aux_linking_fact_distortion":
            return aux_linking_rewrite_fact_distortion().rewrite(
            input_text=input_text,
            model=act_model,
            parser_model=parser_model,
            reflection_privacy=reflection_privacy,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            fact_transformation_instruction=FACT_TRANSFORMATION_INSTRUCTION, 
            fact_rewriting_instruction=FACT_REWRITING_INSTRUCTION,
            document_rewriting_instruction=DOCUMENT_REWRITING_ORIGINAL_REFERENCE_INSTRUCTION,
            current_facts=current_facts,
            original_facts=original_facts,
            current_fact_ids=current_fact_ids,
            fact_history=fact_history,
            fact_transformation_utility_instruction=FACT_TRANSFORMATION_UTILITY_INSTRUCTION,
            privacy_unsatisfied=privacy_unsatisfied,
            conclusions=conclusions,
            )
        elif strategy == "aux_linking":
            return aux_linking_rewrite().rewrite(
                input_text=input_text,
                people=people,
                model=act_model,
                parser_model=parser_model,
                cot=cot,
                prev_rewriting=prev_rewriting,
                reflection_privacy=reflection_privacy,
                privacy_unsatisfied=privacy_unsatisfied,
                detection_result=detection_result,
                no_utility=no_utility,
                whole_task_instruction=WHOLE_TASK_INSTRUCTION,
                general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
                detection_result_prefix=DETECTION_INSTRUCTION,
                simple_rewriting_instruction=SIMPLE_REWRITING_INSTRUCTION,
                simple_rewriting_instruction_cot=SIMPLE_REWRITING_INSTRUCTION_COT,
                reflection_privacy_rewriting_instruction=REFELECTION_PRIVACY_REWRITING_INSTRUCTION,
                aux_privacy_rewriting_instruction=REWRITING_INSTRUCTION_AUX_LINKING_PRIVACY_DBBIO,
                aux_utility_rewriting_instruction=REWRITING_INSTRUCTION_AUX_LINKING_UTILITY,
                language='wiki',
                conclusions=conclusions,
            )


    def privacy_reflex(self, model: ModelBase, rewriting, people, p_threshold, no_utility, retriever):
        return generic_privacy_reflection(
            model=model,
            retriever=retriever,
            curr_rewriting=rewriting,
            people=people,
            p_threshold=p_threshold,
            no_utility=no_utility,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            privacy_reflection_chat_instruction_1=PRIVACY_REFLECTION_INSTRUCTION_1,
            privacy_reflection_completion_instruction_1=PRIVACY_REFLECTION_INSTRUCTION_1,
            privacy_reflection_chat_instruction_2=PRIVACY_REFLECTION_INSTRUCTION_2,
            privacy_reflection_completion_instruction_2=PRIVACY_REFLECTION_INSTRUCTION_2
        )

    def utility_reflex(self, input_text: str, model: ModelBase, rewriting, label, privacy_score=None):
        return generic_utility_reflection(
            input_text=input_text,
            model=model,
            label=label,
            privacy_score=privacy_score,
            curr_rewriting=rewriting,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            utility_reflection_chat_instruction_1=UTILITY_REFLECTION_INSTRUCTION_1,
            utility_reflection_completion_instruction_1=UTILITY_REFLECTION_INSTRUCTION_1,
        )

    def task_agnostic_utility_reflection(self, input_text: str, model: ModelBase, rewriting, conclusions:str):
        return task_agnostic_utility_reflection(
            input_text=input_text,
            model=model,
            curr_rewriting=rewriting,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            utility_reflection_chat_instruction_1=AGNOSTIC_UTILITY_REFLECTION_INSTRUCTION_CONCLUSIONS,
            utility_reflection_completion_instruction_1=AGNOSTIC_UTILITY_REFLECTION_INSTRUCTION_CONCLUSIONS,
            conclusions=conclusions,
        )

    def privacy_confidence_evaluation(self, model: ModelBase, rewriting, people):
        return generic_privacy_confidence_evaluation(
            model=model,
            curr_rewriting=rewriting,
            people=people,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            privacy_confidence_evaluation_instruction=PRIVACY_EVALUATION_CONFIDENCE_INSTRUCTION
        )

    def privacy_selection_evaluation(self, model: ModelBase, rewriting, original_text, people, candidate_list):
        return generic_privacy_selection_evaluation(
            model=model,
            curr_rewriting=rewriting,
            original_text=original_text,
            people=people,
            candidate_list=candidate_list,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            candidate_generation_instruction=PRIVACY_EVALUATION_SELECTION_INSTRUCTION_1,
            privacy_selection_evaluation_instruction=PRIVACY_EVALUATION_SELECTION_INSTRUCTION_2
        )

    def qa_evaluation(self, model, anonymised_text, question, choices, answer_indx):
        return qa_evaluation(
            model=model,
            anonymised_text=anonymised_text,
            question=question,
            choices=choices,
            answer_indx=answer_indx,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
        )

    def privacy_aux_linking(self, model: ModelBase, aux_info_sets: list[list[str]], rewriting, tau, fd):
        return generic_privacy_aux_linking(
            model=model,
            aux_info_sets=aux_info_sets,
            curr_rewriting=rewriting,
            tau=tau,
            general_system_instruction=GENERAL_SYSTEM_INSTRUCTION,
            aux_confidence_instruction=AUX_CONFIDENCE_SCORING_INSTRUCTION,
            feedback_synthesis_instruction= FEEDBACK_SYNTHESIS_INSTRUCTION_FD if fd else FEEDBACK_SYNTHESIS_INSTRUCTION
        )

    def extract_facts_from_dataset(self, dataset, model: ModelBase, log_path:str):
        return extract_facts_from_dataset(dataset, model, log_path, GENERAL_SYSTEM_INSTRUCTION, FACT_EXTRACTION_INSTRUCTION_1)

    def document_conclusions(self, input_text, facts, model, parser_model):
        return document_conclusions(input_text=input_text, facts=facts, model=model, parser_model=parser_model,
                         general_system_instruction=GENERAL_SYSTEM_INSTRUCTION, document_conclusions_instruction=DOCUMENT_CONCLUSIONS_INSTRUCTION)


DUMMY_FUNC_SIG = "def func():"
DUMMY_FUNC_CALL = "func()"


def handle_first_line_indent(func_body: str) -> str:
    if func_body.startswith("    "):
        return func_body
    split = func_body.splitlines()
    return f"    {split[0]}\n" + "\n".join(split[1:])


def handle_entire_body_indent(func_body: str) -> str:
    split = func_body.splitlines()
    res = "\n".join(["    " + line for line in split])
    return res


def fix_turbo_response(func_body: str) -> str:
    return fix_markdown(remove_unindented_signatures(func_body))


def fix_markdown(func_body: str) -> str:
    return re.sub("`{3}", "", func_body)


def remove_unindented_signatures(code: str) -> str:
    regex = r"^def\s+\w+\s*\("

    before_signature = []
    after_signature = []
    signature_found = False

    for line in code.split("\n"):
        if re.match(regex, line):
            signature_found = True
            continue

        if signature_found:
            after_signature.append(line)
        else:
            if not line.startswith("    ") and line.strip():
                line = "    " + line
            before_signature.append(line)

    return "\n".join(before_signature + after_signature)


def py_fix_indentation(func_body: str) -> str:
    func_body = fix_turbo_response(func_body)
    """
    3 cases:
        1. good syntax
        2. first line not good
        3. entire body not good
    """

    def parse_indent_rec(f_body: str, cur_state: int) -> str:
        f_body = fix_markdown(f_body)
        if cur_state > 1:
            return f_body
        code = f'{DUMMY_FUNC_SIG}\n{f_body}\n{DUMMY_FUNC_CALL}'
        try:
            exec(code)
            return f_body
        except (IndentationError, SyntaxError):
            p_func = handle_first_line_indent if cur_state == 0 else handle_entire_body_indent
            return parse_indent_rec(p_func(func_body), cur_state + 1)
        except Exception:
            return f_body

    return parse_indent_rec(func_body, 0)


def py_is_syntax_valid(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False
