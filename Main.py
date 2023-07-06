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
    """This function calls random input generator (fuzzer) to generate initial inputs.

    args:
        random_ipt_dir (str): directory to hold randomly generated inputs.
        random_ast_dir (str): directory to hold randomly generated asts.
        seed_file_base (str): seed input's file name base.
        seed_code (str): seed input code in string.
        user_n (int): user specified N.
        language_info (dict): target language information.

    returns:
        (dict) seed input's ast.
        (dict) new input ids to edited ast node id.
    """

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
    """This function analyze the mutated asts to identify target ast nodes for the next
    phase either to edit or avoid.

    args:
        random_ipt_dir (str): directory to hold randomly generated inputs.
        arguments (dict): user argument.
        ipt_id2edit_node_id (dict): new input ids to edited ast node id.
        seed_ast (dict): seed input's ast.
        random_ast_dir (str): directory to hold randomly generated asts.

    returns:
        (list) list of ast node ids.
        (list) list of buggy input ids.
        (list) list of non-buggy input ids.
    """

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
    """This function calls controlled input generator (fuzzer) to generate inputs,
    which some (or all) will be used in the fault localization.

    args:
        root_path (str): root directory path.
        user_n (int): user specified N.
        controlled_ipt_dir (str): controlled generated input directory.
        controlled_ast_dir (str): controlled mutated ast directory.
        target_ast_node_ids (list) list of ast node ids.
        seed_file_base (str): seed input's file name base.
        seed_ast (dict): seed input's ast.
        language_info (dict): target language information.
        jit_on (list): command-line to execute VM with JIT compilation on.
        jit_off (list): command-line to execute VM with JIT compilation off.

    returns:
        None.
    """

    return JSControlledVariantGenerator.GenerateInputs(
                    root_path, user_n, 
                    controlled_ipt_dir, controlled_ast_dir,
                    target_ast_node_ids, seed_file_base, 
                    seed_ast, language_info, jit_on, jit_off)

def classify_inputs(inputs_path: str, jit_on: list, jit_off: list):
    """This function classifies inputs into buggies and non-buggies.

    args:
        inputs_path (str): directory path where inputs are stored.
        jit_on (list): command-line to execute VM with JIT compilation on.
        jit_off (list): command-line to execute VM with JIT compilation off.

    returns:
        (list) list of buggy input ids.
        (list) list of non-buggy input ids.
    """

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
        seed_path: str, seed_ast: str, last_id: int, inputs_dir: str, 
        buggy_ids: list, nonbuggy_ids: list, user_n: int, random_ipt_dir: list,
        rand_buggy_ids: list, controlled_ipt_dir: str):
    """This function selects inputs to be used in the fault localization generated 
    by the controlled fuzzer.

    args:
        seed_path (str): path to seed input.
        seed_ast (dict): seed input's ast.
        last_id (int): last id+1 of generated controlled input.
        inputs_dir (str): directory path where to store selected inputs.
        buggy_ids (list): list of buggy ids.
        nonbuggy_ids (list): list of non-buggy ids.
        user_n (int): user specified N.
        random_ipt_dir (list): directory path to random inputs.
        rand_buggy_ids (list): list of randomly generated input ids.
        controlled_ipt_dir (str): controlled generated input directory.

    returns:
        (list) list of selected buggy ids.
        (list) list of selected non-buggy ids.
    """

    (
        selected_buggy_ids,
        selected_nonbuggy_ids,
        n_of_buggies,
        n_of_nonbuggies
    ) = SelectInputs.select_input_ids(seed_ast, controlled_ipt_dir, buggy_ids, nonbuggy_ids, user_n)

    (
        selected_buggy_ids,
        selected_nonbuggy_ids
    ) = SelectInputs.move_inputs(
            seed_path, inputs_dir, controlled_ipt_dir, selected_buggy_ids, selected_nonbuggy_ids)

    if len(selected_buggy_ids) == 1:
        SelectInputs.move_buggies_from_rand(
                inputs_dir, random_ipt_dir, last_id, rand_buggy_ids,
                n_of_buggies, len(selected_buggy_ids), selected_buggy_ids, seed_ast)

    return selected_buggy_ids, selected_nonbuggy_ids

def check_selected_inputs(inputs_dir: str, jit_on: list, jit_off: list, selected_b: list, selected_nb: list):
    """This function checks whether the selected inputs are correctly classified or not.

    args:
        inputs_dir (str): inputs directory.
        jit_on (list): command-line to execute VM with JIT compilation on.
        jit_off (list): command-line to execute VM with JIT compilation off.
        selected_b (list): list of selected buggy ids.
        selected_nb (list): list of selected non-buggy ids.

    returns:
        None.
    """

    buggy_ids, nonbuggy_ids = classify_inputs(inputs_dir, jit_on, jit_off)

    for id in selected_b:
        if id not in buggy_ids:
            assert (
                False
            ), f"ERROR: selected_b != buggy_ids. {selected_b} != {buggy_ids}."

    for id in selected_nb:
        if id not in nonbuggy_ids:
            assert (
                False
            ), f"ERROR: selected_nb != nonbuggy_ids. {selected_nb} != {nonbuggy_ids}."

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

    jit_on = [arguments["jitExePath"]]
    jit_on.extend(arguments["jitArguments"])
    jit_on.append(None)
    jit_off = [arguments["jitExePath"], arguments["jitOff"]]
    jit_off.append(None)

    create_dirs(root_path)

    language_info = load_json(lang_info)

    seed_file_base = os.path.splitext(os.path.basename(seed_path))[0]

    with open(seed_path) as f:
        seed_code = f.read()

        seed_ast = None
        ipt_id2edit_node_id = None
        # Random input generation.
        print ("PHASE 1: Generating inputs randomly.")
        (
            seed_ast,
            ipt_id2edit_node_id
        ) = get_random_inputs(
                random_ipt_dir, random_ast_dir, seed_file_base, seed_code, user_n, language_info)
        # Classify inputs.
        rand_buggy_ids, rand_nonbuggy_ids = classify_inputs(random_ipt_dir, jit_on, jit_off)
        print (f"   |__ Generated random buggy inputs: {rand_buggy_ids}")
        print (f"   |__ Generated random non-buggy inputs: {rand_nonbuggy_ids}")
        # If seed_ast does not exist, simply generate one from the seed code.
        if not seed_ast:
            seed_ast = (JSAstG.AstGenerator(seed_code)).toDict()
        # Learn about the randomly generated inputs.
        print ("PHASE 2: Analyzing randomly generated inputs.")
        (
            target_ast_node_ids,
            buggy_ipt_ids,
            jit_on,
            jit_off
        ) = learn_inputs(random_ipt_dir, arguments, ipt_id2edit_node_id, seed_ast, random_ast_dir)
        # Select inputs generated in a controlled way.
        print ("PHASE 3: Generating inputs based on the learning.")
        last_id = get_controlled_inputs(
                    root_path, user_n, 
                    controlled_ipt_dir, controlled_ast_dir,
                    target_ast_node_ids, 
                    seed_file_base, seed_ast, language_info, 
                    jit_on, jit_off)
        # Classify inputs.
        buggy_ids, nonbuggy_ids = classify_inputs(controlled_ipt_dir, jit_on, jit_off)
        print (f"   |__ Generated controlled buggy inputs: {buggy_ids}")
        print (f"   |__ Generated controlled non-buggy inputs: {nonbuggy_ids}")
        # Select buggy and non-buggy input ids to be used in the analysis.
        print ("PHASE 4: Select inputs to use in the fault localization.")
        (
            selected_buggy_ids,
            selected_nonbuggy_ids
        )= get_inputs_to_analyze(
                seed_path, seed_ast, last_id, inputs_dir, buggy_ids, nonbuggy_ids, user_n,
                random_ipt_dir, rand_buggy_ids, controlled_ipt_dir)
        # Check to make sure the selected inputs are correctly classified.
        check_selected_inputs(inputs_dir, jit_on, jit_off, selected_buggy_ids, selected_nonbuggy_ids)

        selected_buggy_ids.sort()
        selected_nonbuggy_ids.sort()

        print (f"   |__ Selected buggy ids: {selected_buggy_ids} ({len(selected_buggy_ids)})")
        print (f"   |__ Selected non-buggy ids: {selected_nonbuggy_ids} ({len(selected_nonbuggy_ids)})")

if __name__ == "__main__":
    main()
