import os, sys
import json
import argparse
import math
import subprocess

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import JavaScript.SharedEditors as SharedEditors
import Shared.SequenceAlignment as SEQAlign

def load_json(json_file: str):
    """This function loads JSON and returns if the file is valid.
    Otherwise, it throws an error and terminates the program.

    args:
        json_file (str): path to json file.

    returns:
        (dict) loaded IR.
    """
        
    try:
        with open(json_file) as f:
            return json.load(f)
    except IOError as x:
        assert False, f"{json_file} cannot be opened."

def compute_similarity(alignment: dict, seed_size: int):
    
    sim_value = 0

    numerator = 0
    denominator = seed_size

    for seed_id, variant_id in alignment.items():
        if seed_id > 0 and variant_id > 0:
            numerator += 1
        if variant_id > 0 and seed_id <= 0:
            denominator += 1

    sim_value = numerator / denominator

    return sim_value

def sort_by_value(target: dict):

    return {k: v for k, v in sorted(target.items(), key=lambda item: item[1])}

def select_input_ids(seed_ast: dict, controlled_ipt_dir: str, buggy_ids: list, nonbuggy_ids: list, user_n: int):

    id2node = {}
    seed_id2nodeStr = {}

    selected_buggy_ids = []
    selected_nonbuggy_ids = []

    depth = SharedEditors.assignIds(seed_ast, 1, id2node)
    for id, node in id2node.items():
        seed_id2nodeStr[id] = str(node)

    input_files = os.listdir(f"{controlled_ipt_dir}")
    ast_files = os.listdir(f"{controlled_ipt_dir}/asts")

    ast_id2sim_value = {}
    for ast_file in ast_files:
        ast = load_json(f"{controlled_ipt_dir}/asts/{ast_file}")
        ast_id = int(ast_file.split('__')[1].split('.')[0])

        id2nodeStr = {}
        depth = SharedEditors.assignIds(ast, 1, id2node)
        for id, node in id2node.items():
            id2nodeStr[id] = str(node)

        alignment = SEQAlign.SequenceAlignment(
                                list(seed_id2nodeStr.values()),
                                list(id2nodeStr.values()))

        sim_value = compute_similarity(alignment, len(seed_id2nodeStr))
        ast_id2sim_value[ast_id] = sim_value

    ast_id2sim_value = sort_by_value(ast_id2sim_value)

    sorted_buggy_ids = []
    sorted_nonbuggy_ids = []

    for ast_id, sim_value in ast_id2sim_value.items():
        if ast_id in buggy_ids:
            sorted_buggy_ids.append(ast_id)
        elif ast_id in nonbuggy_ids:
            sorted_nonbuggy_ids.append(ast_id)
        else:
            assert (
                False
            ), f"ERROR: ast id {ast_id} is neither in buggy nor non-buggy list."

    if user_n % 2 == 0:
        n_of_buggies = int(user_n/2)
        n_of_nonbuggies = int((user_n/2)+1)
    else:
        n_of_buggies = int(math.floor(user_n/2))
        n_of_nonbuggies = int(math.ceil(user_n/2))

    if len(sorted_buggy_ids) <= n_of_buggies:
        selected_buggy_ids = sorted_buggy_ids
    else:
        sorted_buggy_ids.reverse()
        selected_buggy_ids = sorted_buggy_ids[0:n_of_buggies]

    if len(sorted_nonbuggy_ids) <= n_of_nonbuggies:
        selected_nonbuggy_ids = sorted_nonbuggy_ids
    else:
        selected_nonbuggy_ids = sorted_nonbuggy_ids[0:n_of_nonbuggies]

    return selected_buggy_ids, selected_nonbuggy_ids

def select_inputs(
        seed_path: str, input_dir: str, controlled_ipt_dir: str, 
        selected_buggy_ids: list, selected_nonbuggy_ids: list):

    merged = selected_buggy_ids + selected_nonbuggy_ids

    subprocess.run(["cp", seed_path, f"{input_dir}/poc-original__0.js"])

    for ipt_id in merged:
        ctr_ipt_path = f"{controlled_ipt_dir}/poc-variant__{ipt_id}.js"
        ipt_path = f"{input_dir}/poc-variant__{ipt_id}.js"
        
        subprocess.run(["mv", ctr_ipt_path, ipt_path])

    return selected_buggy_ids + [0], selected_nonbuggy_ids
