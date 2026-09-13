import json
import string

from generators.model import ModelBase, Message
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from generators.generator_utils import parse_fixing
from generators.generator_utils import safe_format, make_parser, make_detection_parser, run_generation



REDDIT_FEATURE_MAP = {
    "age": "Age",
    "sex": "Sex",
    "city_country": "Location",
    "birth_city_country": "Place of birth",
    "education": "Education",
    "income_level": "Income level",
    "relationship_status": "Relationship status",
}

class reflexion_rewrite():
    @staticmethod
    def rewrite(
        input_text: str,
        label: str,
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
        reinforcement_learning_instruction: str,
        language: str,
        p_threshold: int,
        utility_score: str,
    ):
        if not no_utility:
            return run_utility_rewrite(
                input_text, label, people, model, parser_model,
                prev_rewriting, reflection_privacy, privacy_unsatisfied,
                general_system_instruction, reinforcement_learning_instruction, language,
                template_kwargs={"p_threshold": p_threshold},
            )
        return run_no_utility_rewrite(
            input_text, model, parser_model, cot, prev_rewriting,
            reflection_privacy, privacy_unsatisfied, detection_result,
            whole_task_instruction, general_system_instruction,
            detection_result_prefix, simple_rewriting_instruction,
            simple_rewriting_instruction_cot,
            reflection_privacy_rewriting_instruction,
        )


def run_utility_rewrite(input_text, label, people, model, parser_model,
                        prev_rewriting, reflection_privacy, privacy_unsatisfied,
                        general_system_instruction, instruction_template, language,
                        template_kwargs):
    """Shared body for the `not no_utility` branch."""
    prev_rewriting = append_privacy_utility_suggestion(
        prev_rewriting, privacy_unsatisfied, language, people,
        reflection_privacy, label,
    )

    response_schemas, output_parser, format_instructions = make_parser(
        "anonymised_text", "your editing result",
    )

    # plain .format here: these templates intentionally omit some of these
    # placeholders, and generate_chat supplies format_instructions itself
    user_content = instruction_template.format(
        format_instructions=format_instructions,
        input_text=input_text,
        prev_rewriting=prev_rewriting,
        **template_kwargs,
    )

    messages = [
        Message(role="system", content=general_system_instruction),
        Message(role='user', content=user_content),
    ]
    return run_generation(
        model, parser_model, general_system_instruction,
        format_instructions, output_parser, response_schemas, messages,
    )



def run_no_utility_rewrite(input_text, model, parser_model, cot, prev_rewriting,
                           reflection_privacy, privacy_unsatisfied, detection_result,
                           whole_task_instruction, general_system_instruction,
                           detection_result_prefix, simple_rewriting_instruction,
                           simple_rewriting_instruction_cot,
                           reflection_privacy_rewriting_instruction):
    """
    Their method is incomplete for this in the original code.
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

def append_privacy_utility_suggestion(prev_rewriting, privacy_unsatisfied, language,
                                      people, reflection_privacy, label):
    """Append the privacy/utility suggestion to prev_rewriting and return it."""
    if privacy_unsatisfied == 'Yes':
        if language == 'wiki':
            prev_rewriting += (
                "Suggestion: You should now focus on improving the privacy score by "
                "preventing the inference of the person's identity. "
                "Sensitive entities that can be used to achieve correct inference are here: "
                f"{reflection_privacy}"
            )
        elif language == 'reddit':
            feature = REDDIT_FEATURE_MAP[list(people.keys())[0]]
            prev_rewriting += (
                "Suggestion: You should now focus on improving the privacy score by "
                f"preventing the inference of the comment author's {feature}. "
                "Sensitive entities that can be used to achieve correct inference are here: "
                f"{reflection_privacy}"
            )
    else:
        prev_rewriting += (
            "Suggestion: You should now improve the utility score about classifying the "
            f"text as {label} without decreasing the privacy score."
        )
    return prev_rewriting