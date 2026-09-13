import os
import argparse
from datetime import datetime, timezone, timedelta
#from immediate_refinement import run_immediate_refinement
#from immediate_reflexion import run_immediate_reflexion

#from simple import run_simple
from anonymisation_methods.aux_linking import run_aux_linking
from anonymisation_methods.aux_linking_fact_distortion import run_aux_linking_fact_distortion
from anonymisation_methods.reflexion import run_reflexion
#from reflexion_ucs import run_reflexion_ucs
from evaluation.privacy.test_acc import run_test_acc
from utils.utils import read_jsonl, read_jsonl_gz
import random
import numpy as np

seed=42


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run_name", type=str, help="The name of the run")
    parser.add_argument("--root_dir", type=str,
                        help="The root logging directory", default="root")
    parser.add_argument("--dataset_path", type=str,
                        help="The path to the benchmark dataset", default="root")
    parser.add_argument("--strategy", type=str,
                        help="Strategy: `simple`, `reflexion`")
    parser.add_argument("--language", type=str, help="Strategy: `py` or `rs`")
    parser.add_argument(
        "--pe_model", type=str, default="gpt-4o", help="OpenAI models only for now.")
    parser.add_argument("--pass_at_k", type=int,
                        help="Pass@k metric", default=1)
    parser.add_argument("--max_iters", type=int,
                        help="The maximum number of self-improvement iterations", default=10)
    parser.add_argument("--expansion_factor", type=int,
                        help="The expansion factor for the reflexion UCS and A* strategy", default=3)

    parser.add_argument("--is_leetcode", action='store_true',
                        help="To run the leetcode benchmark")  # Temporary

    parser.add_argument("--verbose", action='store_true',
                        help="To print live logs")
    parser.add_argument("--no_utility", action='store_true',
                        help="Whether add utility evaluation module")
    parser.add_argument("--cot", action='store_true',
                        help="Whether use COT prompt to generate the initial state")
    parser.add_argument("--mem_len", type=int,
                        help="The maximum length of memory", default=3)
    parser.add_argument("--tau", type=int,
                        help="The privacy score that must be obtained to switch to utility optimisation", default=80)
    parser.add_argument("--u", type=int,
                        help="The number of adversaries in the ensemble", default=5)
    parser.add_argument("--p_threshold", type=int,
                        help="The maximum number of distinguishable people", default=10)
    parser.add_argument("--rag_data_path", type=str, default="./benchmarks/Wiki_People/All_data_for_retrieval.jsonl",
                        help="The path of rag data")
    parser.add_argument("--rag_embed_cache_dir", type=str, default="/home/ember/Desktop/work_space/Anonymization_Experiments/cache_emb",
                        help="The embedding cache directory")
    parser.add_argument("--rag_num", type=int,
                        help="The maximum number of retrieved documents", default=5)
    parser.add_argument(
        "--ue_model", type=str, default="gpt-4o", help="OpenAI models only for now")
    parser.add_argument(
        "--act_model", type=str, default="gpt-4o", help="OpenAI models only for now.")
    parser.add_argument(
        "--parser_model", type=str, default="gpt-4o", help="OpenAI models only for now.")
    parser.add_argument(
        "--seed", type=int, help="Set the seed", default=42)
    parser.add_argument("--num_workers", type=int,
                        help="The number of documents to process in parallel", default=1)

    # TODO: implement this
    # parser.add_argument("--is_resume", action='store_true', help="To resume run")
    # parser.add_argument("--resume_dir", type=str, help="If resume, the logging directory", default="")
    args = parser.parse_args()
    return args


def strategy_factory(strategy: str):
    def kwargs_wrapper_gen(func, delete_keys=[]):
        def kwargs_wrapper(**kwargs):
            for key in delete_keys:
                del kwargs[key]
            return func(**kwargs)
        return kwargs_wrapper

    # if strategy == "simple":
    #     return kwargs_wrapper_gen(run_simple, delete_keys=["expansion_factor", "max_iters", "no_utility", "p_threshold",
    #                                                        "mem_len", "rag_embed_cache_dir", "rag_num", "rag_data_path",
    #                                                        "cot"])
    if strategy == "reflexion":
        return kwargs_wrapper_gen(run_reflexion, delete_keys=["expansion_factor", "facts_path", "tau", "u"])
    # elif strategy == "immediate-reflexion":
    #     return kwargs_wrapper_gen(run_immediate_reflexion, delete_keys=["expansion_factor", "no_utility", "p_threshold",
    #                                                                     "mem_len", "rag_embed_cache_dir", "rag_num"
    #                                                                     , "rag_data_path", "cot"])
    # elif strategy == "immediate-refinement":
    #     return kwargs_wrapper_gen(run_immediate_refinement, delete_keys=["expansion_factor", "no_utility", "p_threshold"
    #                                                                      , "mem_len", "rag_embed_cache_dir", "rag_num",
    #                                                                      "rag_data_path", "cot"])
    # elif strategy == "reflexion-ucs":
    #     return kwargs_wrapper_gen(run_reflexion_ucs)
    elif strategy == "test-acc":
        return kwargs_wrapper_gen(run_test_acc, delete_keys=["expansion_factor", "max_iters", "mem_len", "ue_model_name",
                                                              "facts_path", "tau", "u", "act_model_name","parser_model_name",
                                                              "cot", "num_workers"

                                                              ])
    
    elif strategy == "aux_linking":
        return kwargs_wrapper_gen(run_aux_linking, delete_keys=["expansion_factor", "verbose", "p_threshold", "is_leetcode", "rag_data_path", "rag_num", "rag_embed_cache_dir", "mem_len"])
    
    elif strategy == "aux_linking_fact_distortion":
        return kwargs_wrapper_gen(run_aux_linking_fact_distortion, delete_keys=["expansion_factor", "verbose", "p_threshold", "is_leetcode", "rag_data_path", "rag_num", "rag_embed_cache_dir", "mem_len"])
    
    else:
        raise ValueError(f"Strategy `{strategy}` is not supported")


def main(args):

    if args.seed:
        print(f"Using seed {seed}")
        random.seed(seed)
        np.random.seed(seed)


    # check if the root dir exists and create it if not
    if not os.path.exists(args.root_dir):
        os.makedirs(args.root_dir)

    # get the dataset name
    # dataset_name = os.path.basename(args.dataset_path).replace(".jsonl", "")
    dataset_name = args.language

    # check if log path already exists
    log_dir = str(os.path.join(args.root_dir, args.run_name))
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    

    model_short = args.pe_model.split("/")[-1] if args.strategy == "test-acc" else args.act_model.split("/")[-1]

    parts = [
        args.strategy,
        dataset_name,
        date_str,
        f"model_{model_short}",
        f"seed_{args.seed}",
    ]
    if args.strategy in ("reflexion", "simple"):
        parts.append(f"iters_{args.max_iters}")
        parts.append(f"pak_{args.pass_at_k}")
        parts.append(f"noutil_{args.no_utility}")
        parts.append(f"cot_{args.cot}")
        parts.append(f"mem_{args.mem_len}")
        parts.append(f"pthr_{args.p_threshold}")
    elif args.strategy in ("aux_linking", "aux_linking_fact_distortion"):
        parts.append(f"iters_{args.max_iters}")
        parts.append(f"pak_{args.pass_at_k}")
        parts.append(f"tau_{args.tau}")
        parts.append(f"u_{args.u}")


    filename = "_".join(parts) + ".jsonl"
    log_path = os.path.join(log_dir, filename)

    facts_path = os.path.join(
                            "facts",
                            f"{dataset_name}_facts.jsonl")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # check if the strategy is valid
    run_strategy = strategy_factory(args.strategy)

    # print starting message
    if args.verbose:
        print(f"""
Starting run with the following parameters:
strategy: {args.strategy}
pass@k: {args.pass_at_k}
""")
    else:
        print(f"Logs will be saved in `{log_dir}`")

    # load the dataset
    print(f'Loading the dataset...')
    if args.dataset_path.endswith(".jsonl"):
        dataset = read_jsonl(args.dataset_path)
    elif args.dataset_path.endswith(".jsonl.gz"):
        dataset = read_jsonl_gz(args.dataset_path)
    else:
        raise ValueError(
            f"Dataset path `{args.dataset_path}` is not supported")

    print(f"Loaded {len(dataset)} examples")
    # start the run
    # evaluate with pass@k
    run_strategy(
        dataset=dataset,
        pe_model_name=args.pe_model,
        ue_model_name=args.ue_model,
        act_model_name=args.act_model,
        parser_model_name=args.parser_model,
        language=args.language,
        max_iters=args.max_iters,
        pass_at_k=args.pass_at_k,
        log_path=log_path,
        facts_path=facts_path,
        verbose=args.verbose,
        expansion_factor=args.expansion_factor,
        is_leetcode=args.is_leetcode,
        no_utility=args.no_utility,
        cot=args.cot,
        mem_len=args.mem_len,
        p_threshold=args.p_threshold,
        rag_data_path=args.rag_data_path,
        rag_num=args.rag_num,
        rag_embed_cache_dir=args.rag_embed_cache_dir,
        tau=args.tau,
        u=args.u,
        seed=args.seed,
        num_workers=args.num_workers,
    )

    print(f"Done! Check out the logs in `{log_path}`")


if __name__ == "__main__":
    args = get_args()
    main(args)
