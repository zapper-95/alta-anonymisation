from utils.utils import enumerate_resume, write_jsonl, make_printv
from generators import generator_factory, model_factory
import tqdm
from typing import List
import ezsheets
import time
import json


def run_test_acc(
    dataset: List[dict],
    pe_model_name: str,
    language: str,
    pass_at_k: int,
    log_path: str,
    verbose: bool,
    p_threshold: int,
    no_utility: bool,
    seed:int,
    is_leetcode: bool = False,
    rag_data_path: str = '',
    rag_num: int = 5,
    rag_embed_cache_dir: str = '',
    use_candidate_list=False,
) -> None:
    gen = generator_factory(language)
    model = model_factory(pe_model_name, seed)

    print_v = make_printv(verbose)

    num_items = len(dataset)
    num_success = 0
    confidence_score_list = []
    candidate_list_list = []
    success = []
    result = {}

    if use_candidate_list:
        with open("./evaluation/privacy/db_bio_example_candidate_list.jsonl", "r", encoding="utf-8-sig") as f:
            candidate_data = [json.loads(line) for line in f]


    for i, item in enumerate_resume(tqdm.tqdm(dataset), log_path):
        if language == 'wiki':
            anonymized_text = item['final_text']
            original_text = item['text']
            people = item['people']
            privacy_confidence_evaluation = gen.privacy_confidence_evaluation(model, anonymized_text, people)
        elif language == 'reddit':
            anonymized_text = item['anonymized_response']
            original_text = item['response']
            people = {item['feature']: item['personality'][item['feature']]}
            privacy_confidence_evaluation = gen.privacy_confidence_evaluation(model, anonymized_text, people)
        elif language == "medqa":
            anonymised_text = item["final_text"]
            #anonymised_text = item["comments"][3]["comments"][0]["text"]
            question = item["question"]
            answer = item["answer"]
            privacy_confidence_evaluation = gen.privacy_confidence_evaluation(model, anonymised_text,question,answer)
        
        confidence_score = int(privacy_confidence_evaluation["Confidence Score"])
        confidence_score_list.append(confidence_score)

        if language == 'wiki':
            if use_candidate_list:
                candidate_list = candidate_data[i]["candidate_list"]
            else:
                candidate_list = None

            privacy_selection_evaluation = gen.privacy_selection_evaluation(model, anonymized_text, original_text, people,
                                                                            candidate_list)
            if not use_candidate_list:
                candidate_list_list.append(privacy_selection_evaluation["candidate_list"])

        elif language == 'reddit':
            feature = list(people.keys())[0]
            if feature in ['age', 'city_country', 'birth_city_country', 'education', 'relationship_status']:
                if "candidate_list" in item.keys():
                    candidate_list = item['candidate_list']
                else:
                    candidate_list = None
                privacy_selection_evaluation = gen.privacy_selection_evaluation(model, anonymized_text, original_text,
                                                                                people,
                                                                                candidate_list)
                if "candidate_list" not in item.keys():
                    candidate_list_list.append(privacy_selection_evaluation["candidate_list"])
            else:
                assert feature in ['sex', 'income_level']
                candidate_list = None
                privacy_selection_evaluation = gen.privacy_selection_evaluation(model, anonymized_text, original_text,
                                                                                people,
                                                                                candidate_list)
                if "candidate_list" not in item.keys():
                    candidate_list_list.append(['None'])

        elif language == "medqa":
            choices = item ["choices"]
            answer_indx = item["answer_indx"]

            privacy_selection_evaluation = gen.qa_evaluation(model, anonymised_text, question, choices, answer_indx)
    
        if privacy_selection_evaluation["success"]:
            num_success += 1
            success.append(True)
        else:
            num_success += 0
            success.append(False)

        print_v(
            f'completed {i+1}/{num_items}: acc = {round(num_success/(i+1), 2)}')
    result['confidence_score'] = confidence_score_list
    result['rank_avg'] = sum(confidence_score_list)/len(confidence_score_list)
    result['success'] = success
    result['success_rate'] = num_success/num_items
    result['num_success'] = num_success
    result['candidate_list'] = candidate_list_list
    model.print_usage()
    print(f"log path: {log_path}\n")
    write_jsonl(log_path, [result], append=False)
