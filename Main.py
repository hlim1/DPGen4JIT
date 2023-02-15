import os, sys
import json
import argparse

import JavaScript.JSRandomVariantGenerator as JSRandomVariantGenerator
import JavaScript.JSVariantLearning as JSVariantLearning
import JavaScript.JSControlledVariantGenerator as JSControlledVariantGenerator
import JavaScript.SharedEditors as SharedEditors

def argument_parser():
    """This function parses the passed argument.

    args:
        None

    returns:
        (str) file path.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="A file that holds all the command-line arugments to process."
    )
    args = parser.parse_args()

    return args.file

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

def create_dirs(root: str):
    """This function checks the existence of the directories
    and create new ones if one does not exist. Then, sets 
    the global path to it.

    args:
        root (str): root directoy path.

    returns:
        None.
    """

    if not os.path.exists(f"{root}/random"):
        os.makedirs(f"{root}/random")
    if not os.path.exists(f"{root}/random/asts"):
        os.makedirs(f"{root}/random/asts")
    if not os.path.exists(f"{root}/inputs"):
        os.makedirs(f"{root}/inputs")
    if not os.path.exists(f"{root}/inputs/asts"):
        os.makedirs(f"{root}/inputs/asts")

def get_random_inputs(
        random_ipt_dir: str, random_ast_dir: str, seed_file_base: str, seed_code: str, 
        user_n: int, language_info: dict):

    (
        seed_ast,
        ipt_id2edit_node_id
    ) = JSRandomVariantGenerator.RandomVariantGenerator(
            random_ipt_dir, 
            random_ast_dir, 
            seed_file_base, 
            seed_code, 
            user_n, 
            language_info)

    return seed_ast, ipt_id2edit_node_id

def learn_inputs(random_ipt_dir: str, arguments: dict, ipt_id2edit_node_id: dict):

    (
        target_ast_node_ids,
        buggy_ipt_ids,
        jit_on,
        jit_off
    ) = JSVariantLearning.Learning(random_ipt_dir, arguments, ipt_id2edit_node_id)

    return target_ast_node_ids, buggy_ipt_ids, jit_on, jit_off

def main():
    arguments_json = argument_parser()
    arguments = load_json(arguments_json)

    root_path = arguments["root"]
    seed_path = arguments["seed"]
    lang_info = arguments["language_info"]
    user_n    = arguments["n"]

    random_ipt_dir = f"{root_path}/random"
    random_ast_dir = f"{root_path}/random/asts"
    controlled_ipt_dir = f"{root_path}/inputs"
    controlled_ast_dir = f"{root_path}/inputs/asts"

    create_dirs(root_path)

    language_info = load_json(lang_info)

    seed_file_base = os.path.splitext(os.path.basename(seed_path))[0]

    with open(seed_path) as f:
        seed_code = f.read()

        ipt_id2edit_node_id = None
        # Random input generation.
        (
            seed_ast,
            ipt_id2edit_node_id
        ) = get_random_inputs(random_ipt_dir, random_ast_dir, seed_file_base, seed_code, user_n, language_info)
        # Learn about the randomly generated inputs.
        (
            target_ast_node_ids,
            buggy_ipt_ids,
            jit_on,
            jit_off
        ) = learn_inputs(random_ipt_dir, arguments, ipt_id2edit_node_id)

        # DEBUG
        poc_1_ast = load_json("./random/asts/poc-variant__1.json")
        count = 0
        id2node = {}
        #count = SharedEditors.treeScanner(poc_1_ast, count)
        count = SharedEditors.assignIds(seed_ast, count, id2node)
        print ("Node ID To Node:")
        for id, node in id2node.items():
            print (f"id : node = {id} : {node}")
        print (f"count = {count}")
        print (f"edited_node_ids = {list(ipt_id2edit_node_id.values())}")

    return

if __name__ == "__main__":
    main()
