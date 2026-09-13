import json
import string

from generators.model import ModelBase, Message
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from generators.generator_utils import parse_fixing
from generators.generator_utils import safe_format, make_parser, make_detection_parser, run_generation

class simple_rewrite():
    @staticmethod
    def rewrite(
        input_text: str,
        model: ModelBase,
        parser_model: ModelBase,
        cot: bool,
        detection_result,
        whole_task_instruction: str,
        general_system_instruction: str,
        detection_result_prefix: str,
        simple_rewriting_instruction: str,
        simple_rewriting_instruction_cot: str,
    ):
        response_schemas_2, output_parser_2, format_instructions_2 = make_parser(
            "anonymised_text", "your anonymization result",
        )

        messages = [Message(role="system", content=general_system_instruction)]

        if cot:
            messages.extend(build_cot_detection_messages(
                whole_task_instruction, detection_result_prefix, input_text, detection_result,
                simple_rewriting_instruction_cot.format(format_instructions_2=format_instructions_2),
            ))
        else:
            messages.append(Message(
                role="user",
                content=simple_rewriting_instruction.format(
                    format_instructions_2=format_instructions_2, input_text=input_text,
                ),
            ))

        return run_generation(
            model, parser_model, general_system_instruction,
            format_instructions_2, output_parser_2, response_schemas_2, messages,
        )


def build_cot_detection_messages(whole_task_instruction, detection_result_prefix,
                                 input_text, detection_result, followup_content):
    """The shared 3-message CoT block: task+detection prompt, prior detection, follow-up."""
    format_instructions_1 = make_detection_parser()
    return [
        Message(
            role="user",
            content=(
                f"{whole_task_instruction}\n\n"
                f"{detection_result_prefix.format(format_instructions_1=format_instructions_1, input_text=input_text)}"
            ),
        ),
        Message(role="assistant", content=str(detection_result)),
        Message(role="user", content=followup_content),
    ]