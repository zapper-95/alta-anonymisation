from .generator_types import Generator
from .rewriter import ReWriter
from .med_rewriter import MedReWriter
from .model import GPT5, CodeLlama, ModelBase, GPT4, GPT35, StarChat, GPTDavinci, OpenChat, LLama


def generator_factory(lang: str) -> Generator:
    if lang == "wiki":
        return ReWriter()
    elif lang=="medqa":
        return MedReWriter()
    else:
        raise ValueError(f"Invalid language for generator: {lang}")


def model_factory(model_name: str, seed:int) -> ModelBase:
    if model_name in {"gpt-5.4", "gpt-5.4-mini"}:
        return GPT5(name=model_name, seed=seed)
    elif model_name in {"meta-llama/Llama-3.3-70B-Instruct"}:
        return LLama(name=model_name, seed=seed)
    elif model_name in {"gpt-4", "gpt4-turbo-128k", "gpt-4-turbo-preview", "gpt-4o"}:
        return GPT4(name=model_name, seed=seed)
    elif model_name == "gpt-35-turbo-0301":
        return GPT35(name=model_name)
    elif model_name == "starchat":
        return StarChat()
    elif model_name in {"mistralai/Mixtral-8x7B-Instruct-v0.1", "codellama/CodeLlama-70b-Instruct-hf",
                        "meta-llama/Llama-2-70b-chat-hf", "01-ai/Yi-34B-Chat", "meta-llama/Meta-Llama-3-70B-Instruct",
                        "mistralai/Mixtral-8x22B-Instruct-v0.1"}:
        return OpenChat(name=model_name)
    elif model_name.startswith("codellama"):
        # if it has `-` in the name, version was specified
        kwargs = {}
        if "-" in model_name:
            kwargs["version"] = model_name.split("-")[1]
        return CodeLlama(**kwargs)
    elif model_name.startswith("text-davinci"):
        return GPTDavinci(model_name)
    else:
        raise ValueError(f"Invalid model name: {model_name}")
