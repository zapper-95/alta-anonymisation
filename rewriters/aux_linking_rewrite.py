import json
import string

from generators.model import ModelBase, Message
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from generators.generator_utils import parse_fixing
from generators.generator_utils import safe_format, make_parser, make_detection_parser, run_generation

class aux_linking_rewrite():
    @staticmethod
    def rewrite(
        input_text: str,
        people,
        model: ModelBase,
        parser_model: ModelBase,
        cot: bool,
        prev_rewriting,
        reflection_privacy,
        privacy_unsatisfied,
        detection_result,
        no_utility,
        whole_task_instruction: str,
        general_system_instruction: str,
        detection_result_prefix: str,
        simple_rewriting_instruction: str,
        simple_rewriting_instruction_cot: str,
        reflection_privacy_rewriting_instruction: str,
        aux_privacy_rewriting_instruction: str,
        aux_utility_rewriting_instruction: str,
        language: str,
        conclusions,
    ):
        if not no_utility:
            template = (aux_privacy_rewriting_instruction
                        if privacy_unsatisfied == 'Yes'
                        else aux_utility_rewriting_instruction)
            return run_aux_rewrite(
                input_text, model, parser_model,
                prev_rewriting, reflection_privacy,
                general_system_instruction, template, conclusions,
            )
        return run_no_utility_rewrite(
            input_text, model, parser_model, cot, prev_rewriting,
            reflection_privacy, privacy_unsatisfied, detection_result,
            whole_task_instruction, general_system_instruction,
            detection_result_prefix, simple_rewriting_instruction,
            simple_rewriting_instruction_cot,
            reflection_privacy_rewriting_instruction,
        )


def run_aux_rewrite(input_text, model, parser_model,
                    prev_rewriting, reflection_privacy,
                    general_system_instruction, instruction_template, conclusions):
    """Shared body for the aux-linking `not no_utility` branch. The template
    is chosen by the caller based on the current mode (privacy vs utility)."""
    response_schemas, output_parser, format_instructions = make_parser(
        "anonymised_text", "your editing result",
    )

    user_content = instruction_template.format(
        format_instructions=format_instructions,
        input_text=input_text,
        prev_rewriting=prev_rewriting,
        conclusions=conclusions,
        reflection_privacy=reflection_privacy,
    )

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(role='user', content=user_content),
    ]
    return run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages,
    )

def run_aux_utility_rewrite(input_text, people, model, parser_model,
                            prev_rewriting, reflection_privacy, privacy_unsatisfied,
                            general_system_instruction, instruction_template, language,
                            conclusions):
    """Shared body for the aux-linking `not no_utility` branch."""
    prev_rewriting = append_aux_privacy_utility_suggestion(
        prev_rewriting, privacy_unsatisfied, language, people, reflection_privacy,
    )

    response_schemas, output_parser, format_instructions = make_parser(
        "anonymised_text", "your editing result",
    )

    user_content = instruction_template.format(
        format_instructions=format_instructions,
        input_text=input_text,
        prev_rewriting=prev_rewriting,
        conclusions=conclusions,
        reflection_privacy=reflection_privacy,
    )

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(role='user', content=user_content),
    ]
    return run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages,
    )


def append_aux_privacy_utility_suggestion(prev_rewriting, privacy_unsatisfied, language,
                                          people, reflection_privacy):
    """
    Append the aux-linking privacy/utility suggestion to prev_rewriting and return it.

    The aim in privacy mode is to reduce the adversary's confidence in linking
    auxiliary information to the document, rather than only masking identifiers.
    Utility mode is task-agnostic: no label is referenced. Conclusions to preserve
    and adversary feedback are supplied to the rewriter via the instruction template.
    """
    if privacy_unsatisfied == 'Yes':
        prev_rewriting += (
            "Suggestion: You should now focus on improving the privacy score by "
            "preventing re-identification through auxiliary information. "
            "The adversary's feedback linking auxiliary information to this document is:\n"
            f"{reflection_privacy}"
        )
    else:
        prev_rewriting += (
            "Suggestion: You should now improve the utility score without "
            "decreasing the privacy score, while preserving the conclusions "
            "and inferences that can be drawn from the original document."
        )
    return prev_rewriting


def run_no_utility_rewrite(input_text, model, parser_model, cot, prev_rewriting,
                           reflection_privacy, privacy_unsatisfied, detection_result,
                           whole_task_instruction, general_system_instruction,
                           detection_result_prefix, simple_rewriting_instruction,
                           simple_rewriting_instruction_cot,
                           reflection_privacy_rewriting_instruction):
    """
    RUPTAs method is incomplete for this in the original code.
    We do not inted for our methods to be run with 'no_utility' and so we do not adapt their incomplete method described here.
    """
    response_schemas_2 = [
        ResponseSchema(name="Anonymised text", description="your anonymisation result")
    ]
    output_parser_2 = StructuredOutputParser.from_response_schemas(response_schemas_2)
    format_instructions_2 = output_parser_2.get_format_instructions()
    response_schemas_3 = [
        ResponseSchema(name="Anonymised text", description="your further anonymisation result")
    ]
    output_parser_3 = StructuredOutputParser.from_response_schemas(response_schemas_3)
    format_instructions_3 = output_parser_3.get_format_instructions()

    messages = [
        Message(
            role="system",
            content=general_system_instruction,
        )
    ]
    if cot:
        response_schemas_1 = [
            ResponseSchema(name="People", description="name of the detected people separated by ', '"),
            ResponseSchema(
                name="Sensitive entities",
                description="the list of detected sensitive entities where every two entities are separated by ', '",
            ),
        ]
        output_parser_1 = StructuredOutputParser.from_response_schemas(response_schemas_1)
        format_instructions_1 = output_parser_1.get_format_instructions()
        messages.extend(
            [
                Message(
                    role="user",  # TODO: check this
                    content=f"{whole_task_instruction}\n\n{detection_result_prefix.format(format_instructions_1=format_instructions_1, input_text=input_text)}",
                ),
                Message(
                    role="assistant",  # TODO: check this
                    content=f"{detection_result}",
                ),
                Message(
                    role="user",
                    content=f"{simple_rewriting_instruction_cot.format(format_instructions_2=format_instructions_2)}",
                )
            ]
        )
    else:
        messages.extend(
            [
                Message(
                    role="user",
                    content=f"{simple_rewriting_instruction.format(format_instructions_2=format_instructions_2, input_text=input_text)}",
                ),
                Message(
                    role="assistant",
                    content=prev_rewriting
                )
            ]
        )
    assert privacy_unsatisfied == 'Yes'
    messages.append(
        Message(
            role="user",
            content=f"{reflection_privacy_rewriting_instruction.format(format_instructions_3=format_instructions_3, reflection_privacy=reflection_privacy)}",
        )
    )
    output_dict = model.generate_chat(messages=messages, format_instructions=format_instructions_3,
                                        parser=output_parser_3)
    if output_dict['parse_success'] is False:
        output_dict = parse_fixing(general_system_instruction, format_instructions_3, output_parser_3,
                                    output_dict, parser_model, [d.name for d in response_schemas_3])