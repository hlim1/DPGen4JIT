import os, sys
import json
import argparse
import math

import JavaScript.JSRandomVariantGenerator as JSRandomVariantGenerator
import JavaScript.JSVariantLearning as JSVariantLearning
import JavaScript.JSControlledVariantGenerator as JSControlledVariantGenerator
import JavaScript.SharedEditors as SharedEditors
import JavaScript.JSAstGenerator as JSAstG
import Shared.SequenceAlignment as SEQAlign
import Shared.SelectInputs as SelectInputs

JSEXT = ".js"

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
    if not os.path.exists(f"{root}/controlled"):
        os.makedirs(f"{root}/controlled")
    if not os.path.exists(f"{root}/controlled/asts"):
        os.makedirs(f"{root}/controlled/asts")
    if not os.path.exists(f"{root}/inputs"):
        os.makedirs(f"{root}/inputs")
    if not os.path.exists(f"{root}/misc"):
        os.makedirs(f"{root}/misc")

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

def learn_inputs(
        random_ipt_dir: str, arguments: dict, ipt_id2edit_node_id: dict, seed_ast: dict, 
        random_ast_dir: str):

    (
        target_ast_node_ids,
        buggy_ipt_ids,
        jit_on,
        jit_off
    ) = JSVariantLearning.Learning(
            random_ipt_dir, arguments, ipt_id2edit_node_id, seed_ast, random_ast_dir)

    return target_ast_node_ids, buggy_ipt_ids, jit_on, jit_off

def get_controlled_inputs(
        root_path: str, user_n: int, 
        controlled_ipt_dir: str, controlled_ast_dir: str,
        target_ast_node_ids: list, seed_file_base: str, 
        seed_ast: dict, language_info: dict, jit_on: list, jit_off: list):

    last_ipt_id = JSControlledVariantGenerator.GenerateInputs(
                        root_path, user_n, 
                        controlled_ipt_dir, controlled_ast_dir,
                        target_ast_node_ids, seed_file_base, 
                        seed_ast, language_info, jit_on, jit_off)

    buggy_ids, nonbuggy_ids = classify_inputs(controlled_ipt_dir, jit_on, jit_off)

    if len(buggy_ids) < user_n:
        JSControlledVariantGenerator.GenerateBuggies(
                        root_path, user_n, 
                        controlled_ipt_dir, controlled_ast_dir,
                        target_ast_node_ids, seed_file_base, 
                        seed_ast, language_info, jit_on, jit_off, last_ipt_id)

def classify_inputs(inputs_path: str, jit_on: list, jit_off: list):

    buggy_ids = []
    nonbuggy_ids = []

    inputs = os.listdir(inputs_path)

    for input_file in inputs:
        if input_file.endswith(JSEXT):
            input_path = f"{inputs_path}/{input_file}"
            input_id = int(input_file.split('__')[1].split('.')[0])

            jit_on[-1] = input_path
            jit_off[-1] = input_path

            jitOnOut = JSVariantLearning.RunJITExe(jit_on)
            jitOffOut = JSVariantLearning.RunJITExe(jit_off)

            is_buggy = True
            if (
                    str(jitOnOut.returncode) == '0'
                    and jitOnOut.stdout == jitOffOut.stdout
            ):
                is_buggy = False
            elif (
                    str(jitOnOut.returncode) != '0'
                    and jitOnOut.stdout == jitOffOut.stdout
            ):
                is_buggy = False

            if is_buggy:
                buggy_ids.append(input_id)
            else:
                nonbuggy_ids.append(input_id)

    return buggy_ids, nonbuggy_ids

def get_inputs_to_analyze(
        seed_path: str, seed_ast: str, controlled_ipt_dir: str, inputs_dir: str, 
        buggy_ids: list, nonbuggy_ids: list, user_n: int):

    (
        selected_buggy_ids,
        selected_nonbuggy_ids
    ) = SelectInputs.select_input_ids(seed_ast, controlled_ipt_dir, buggy_ids, nonbuggy_ids, user_n)

    (
        selected_buggy_ids,
        selected_nonbuggy_ids
    ) = SelectInputs.select_inputs(
            seed_path, inputs_dir, controlled_ipt_dir, selected_buggy_ids, selected_nonbuggy_ids)

    return selected_buggy_ids, selected_nonbuggy_ids

def main():
    arguments_json = argument_parser()
    arguments = load_json(arguments_json)

    root_path = arguments["root"]
    seed_path = arguments["seed"]
    lang_info = arguments["language_info"]
    user_n    = arguments["n"]

    random_ipt_dir = f"{root_path}/random"
    random_ast_dir = f"{root_path}/random/asts"
    controlled_ipt_dir = f"{root_path}/controlled"
    controlled_ast_dir = f"{root_path}/controlled/asts"
    inputs_dir = f"{root_path}/inputs"

    create_dirs(root_path)

    language_info = load_json(lang_info)

    seed_file_base = os.path.splitext(os.path.basename(seed_path))[0]

    with open(seed_path) as f:
        seed_code = f.read()

        seed_ast = None
        ipt_id2edit_node_id = None
        # Random input generation.
        (
            seed_ast,
            ipt_id2edit_node_id
        ) = get_random_inputs(
                random_ipt_dir, random_ast_dir, seed_file_base, seed_code, user_n, language_info)
        # If seed_ast does not exist, simply generate one from the seed code.
        if not seed_ast:
            seed_ast = (JSAstG.AstGenerator(seed_code)).toDict()
        # Learn about the randomly generated inputs.
        (
            target_ast_node_ids,
            buggy_ipt_ids,
            jit_on,
            jit_off
        ) = learn_inputs(random_ipt_dir, arguments, ipt_id2edit_node_id, seed_ast, random_ast_dir)
        # Select inputs generated in a controlled way.
        get_controlled_inputs(
                root_path, user_n, 
                controlled_ipt_dir, controlled_ast_dir,
                target_ast_node_ids, 
                seed_file_base, seed_ast, language_info, 
                jit_on, jit_off)
        # Classify inputs.
        buggy_ids, nonbuggy_ids = classify_inputs(controlled_ipt_dir, jit_on, jit_off)
        # Select buggy and non-buggy input ids to be used in the analysis.
        (
            selected_buggy_ids,
            selected_nonbuggy_ids
        )= get_inputs_to_analyze(
                seed_path,seed_ast, controlled_ipt_dir, inputs_dir, buggy_ids, nonbuggy_ids, user_n)

        selected_buggy_ids.sort()
        selected_nonbuggy_ids.sort()

        print (f"Selected buggy ids: {selected_buggy_ids}")
        print (f"Selected non-buggy ids: {selected_nonbuggy_ids}")

    return

if __name__ == "__main__":
    main()
