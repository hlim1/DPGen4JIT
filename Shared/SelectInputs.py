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

JSEXT = ".js"

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
    """This function computes the jaccard similarity value of two sets,
    i.e., seed ast nodes and comparing ast nodes.

    args:
        alignment (dict): seed ast node to comparing ast node alignment result.
        seed_size (int): number of seed ast nodes.

    returns:
        (float) computed jaccard similarity value.
    """
    
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
    """This function sorts dictionary using the values in ascending order.

    args:
        target (dict): dictionary to sort.

    returns:
        (dict): sorted dictionary.
    """

    return {k: v for k, v in sorted(target.items(), key=lambda item: item[1])}

def select_input_ids(
        seed_ast: dict, controlled_ipt_dir: str, buggy_ids: list, 
        nonbuggy_ids: list, user_n: int):
    """This function selects ids of inputs to be used in the analysis.

    args:
        seed_ast (dict): seed input's ast.
        controlled_ipt_dir (str): controlled generated input directory.
        buggy_ids (list): list of buggy ids.
        nonbuggy_ids (list): list of non-buggy ids.
        user_n (int): user specified N.

    returns:
        (list) list of selected buggy ids.
        (list) list of selected non-buggy ids.
    """

    id2node = {}
    seed_id2nodeStr = {}

    selected_buggy_ids = []
    selected_nonbuggy_ids = []

    # Using DFS, traverse the seed ast and assign id to each visited node.
    depth = SharedEditors.assignIds(seed_ast, 1, id2node)
    for id, node in id2node.items():
        seed_id2nodeStr[id] = str(node)

    input_files = os.listdir(f"{controlled_ipt_dir}")
    ast_files = os.listdir(f"{controlled_ipt_dir}/asts")

    # For every generated mutated ast by the controlled fuzzer, 
    # compute the similarity value compared to the seed ast.
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

    # Sort the ast ids in ascending order of similarity values.
    ast_id2sim_value = sort_by_value(ast_id2sim_value)

    # Classify the buggy and non-buggy input ids while maintaining
    # the sorted order.
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

    # Compute the number of buggies and non-buggies to select
    # depends on the user specified N.
    if user_n % 2 == 0:
        n_of_buggies = int(user_n/2)
        n_of_nonbuggies = int(user_n/2)
    else:
        n_of_buggies = int(math.floor(user_n/2))
        n_of_nonbuggies = int(math.ceil(user_n/2))

    # If the generated buggy inputs are less or equal to the target number
    # to select, simply select all generated inputs. Otherwise, reverse the
    # sorted buggy ids as we want to select the most different inputs, then
    # select from first input to target number of inputs.
    if len(sorted_buggy_ids) <= n_of_buggies:
        selected_buggy_ids = sorted_buggy_ids
    else:
        sorted_buggy_ids.reverse()
        selected_buggy_ids = sorted_buggy_ids[0:n_of_buggies]

    # If the generated non-buggy inputs are less or equal to the target number
    # to select, simply select all generated inputs. Otherwise, select
    # from first input to target number of inputs.
    if len(sorted_nonbuggy_ids) <= n_of_nonbuggies:
        selected_nonbuggy_ids = sorted_nonbuggy_ids
    else:
        selected_nonbuggy_ids = sorted_nonbuggy_ids[0:n_of_nonbuggies]

    return selected_buggy_ids, selected_nonbuggy_ids, n_of_buggies, n_of_nonbuggies

def move_inputs(
        seed_path: str, input_dir: str, controlled_ipt_dir: str, 
        selected_buggy_ids: list, selected_nonbuggy_ids: list):
    """This function move selected inputs from the controlled input directory
    to the actual inputs directory where the fault localizer retrieves inputs.

    args:
        seed_path (str): path to seed input.
        inputs_dir (str): directory path where to store selected inputs.
        controlled_ipt_dir (str): controlled generated input directory.
        selected_buggy_ids (list): list of selected buggy ids.
        selected_nonbuggy_ids (list): list of selected non-buggy ids.

    returns:
        (list) list of selected buggy ids.
        (list) list of selected non-buggy ids.
    """

    merged = selected_buggy_ids + selected_nonbuggy_ids

    subprocess.run(["cp", seed_path, f"{input_dir}/poc-original__0.js"])

    for ipt_id in merged:
        ctr_ipt_path = f"{controlled_ipt_dir}/poc-variant__{ipt_id}.js"
        ipt_path = f"{input_dir}/poc-variant__{ipt_id}.js"
        assert (
            os.path.exists(ctr_ipt_path)
        ), f"ERROR: Controlled input {ctr_ipt_path} does not exists."
        subprocess.run(["mv", ctr_ipt_path, ipt_path])

    return selected_buggy_ids + [0], selected_nonbuggy_ids

def move_buggies_from_rand(
        input_dir: str, random_ipt_dir: str, last_id: int, rand_buggy_ids: list,
        n_of_buggies: int, current_n: int, selected_buggy_ids: list, seed_ast: dict):
    """This function moves randomly generated buggy inputs to the inputs/ directory.

    args:
        inputs_dir (str): directory path where to store selected inputs.
        random_ipt_dir (list): directory path to random inputs.
        last_id (int): last id+1 of generated controlled input.
        rand_buggy_ids (list): list of randomly generated input ids.
        n_of_buggies (int): number of buggy inputs expected to be in the inputs/ directory.
        current_n (int): number of buggy inputs actually in the inputs/ directory.
        selected_buggy_ids (list): list of buggy input ids.
        seed_ast (dict): seed input's ast.

    returns:
        None.
    """

    rand_ipts = os.listdir(random_ipt_dir)
    ast_files = os.listdir(f"{random_ipt_dir}/asts")

    id2node = {}
    seed_id2nodeStr = {}
    # Using DFS, traverse the seed ast and assign id to each visited node.
    depth = SharedEditors.assignIds(seed_ast, 1, id2node)
    for id, node in id2node.items():
        seed_id2nodeStr[id] = str(node)

    # For every generated mutated ast by the random input fuzzer, 
    # compute the similarity value compared to the seed ast.
    ast_id2sim_value = {}
    for ast_file in ast_files:
        ast = load_json(f"{random_ipt_dir}/asts/{ast_file}")
        ast_id = int(ast_file.split('__')[1].split('.')[0])

        if ast_id in rand_buggy_ids:
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
    ast_ids = list(ast_id2sim_value.keys())
    # Since we want to select the inputs that are most differnt to the
    # seed input, we reverse the ast ids.
    ast_ids.reverse()

    last_id = last_id + 1

    n_to_move = n_of_buggies

    # Move buggy variants from the random directory to the inputs/ directory.
    for ast_id in ast_ids:
        rand_ipt_path = f"{random_ipt_dir}/poc-variant__{ast_id}.js"
        assert (
            os.path.exists(rand_ipt_path)
        ), f"ERROR: Random input {rand_ipt_path} does not exists."
        ipt_path = f"{input_dir}/poc-variant__{last_id}.js"
        selected_buggy_ids.append(last_id)
        subprocess.run(["mv", rand_ipt_path, ipt_path])
        last_id += 1
        n_to_move -= 1

        if n_to_move == 0:
            break
