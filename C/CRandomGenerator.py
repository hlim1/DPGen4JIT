import copy
import os, sys
import random

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.Shared as Shared

def CRandomGenerator(ast_dict: dict, lang_info: dict):
    """This function randomly mutates the seed program and generates
    user specified amont of new test programs.

    args:
        ast_dict (dict): seed program's ast.
        lang_info (dict): C language specification information.

    returns:
        (list) list of new test program asts.
    """

    nodetypes = Shared.load_json(f"{currentdir}/NodeTypes.json")

    labels = set()
    skip_ids = set()
    function_names = set()
    (
        total_nodes 
    ) = Shared.treeScanner(
            ast_dict, 1, skip_ids, function_names, 
            nodetypes, labels)

    # Tracks the number of generated variants number.
    generated = 1
    # Sets the target_node_id to 1.
    target_node_id = 1
    # List of generated new ASTs.
    asts = [ast_dict]
    # File ID to edited node ID.
    fileId2NodeId = {}

    # Call ast_editor function to modify the original 
    # input program's AST.
    idx = 1
    for i in range(1, total_nodes):
        if i in skip_ids:
            continue
        else:
            edited_nodeId = [-1]
            for j in range(0, 3):
                ast_copy = copy.deepcopy(ast_dict)
                depth = Shared.astEditor(
                            ast_copy, i, lang_info, 1, 
                            skip_ids, function_names,
                            nodetypes, labels, edited_nodeId)
                if (
                    ast_copy not in asts and 
                    edited_nodeId[0] != -1
                ):
                        asts.append(ast_copy)
                        (
                            fileId2NodeId[idx]
                        ) = copy.deepcopy(edited_nodeId[0])
                        idx += 1
    
    print (f"Number of generated new ASTs: {len(asts)-1}...")

    return asts, fileId2NodeId

