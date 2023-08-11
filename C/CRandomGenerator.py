import copy
import os, sys
import random

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.Shared as Shared

def CRandomGenerator(ast_dict: dict, lang_info: dict, user_n: int):
    """This function randomly mutates the seed program and generates
    user specified amont of new test programs.

    args:
        ast_dict (dict): seed program's ast.
        lang_info (dict): C language specification information.
        user_n (int): user specified n.

    returns:
        (list) list of new test program asts.
    """

    skip_ids = set()
    total_nodes = Shared.treeScanner(ast_dict, 1, skip_ids)
    # DEBUG
    print (f"Skip IDS: {skip_ids}")

    # Tracks the number of generated variants number.
    generated = 1
    # Sets the target_node_id to 1.
    target_node_id = 1
    # AST node id to edited info.
    id2edit = {}
    # List of generated new ASTs.
    asts = [ast_dict]

    # Call ast_editor function to modify the original 
    # input program's AST.
    for i in range(1, total_nodes):
        if i in skip_ids:
            continue
        else:
            for j in range(0, 5):
                ast_copy = copy.deepcopy(ast_dict)
                depth = Shared.ast_editor(
                            ast_copy, i, lang_info, id2edit, 
                            1, skip_ids)
                if ast_copy not in asts:
                    asts.append(ast_copy)
    
    print (f"Number of generated new ASTs: {len(asts)-1}...")

    return asts

