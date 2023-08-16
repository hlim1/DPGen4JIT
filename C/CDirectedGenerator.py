import copy
import os, sys
import random

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.Shared as Shared

def CDirectedGenerator(ast_dict: dict, lang_info: dict, nodeIds: set, user_n: int):
    """This function directed the AST editor to target and mutate
    specific nodes.

    args:
        ast_dict (dict): seed program's ast.
        lang_info (dict): C language specification information.
        nodeIds (set): set of target node IDs.
        user_n (int):

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

    # Targeting the identifies node IDs, attempt to generate non-buggy 
    # C programs.
    nonBuggyAsts = GenerateNonBuggies(
            ast_dict, lang_info, nodeIds, labels, 
            skip_ids, function_names, nodetypes)
    # Generate new buggy program ASTs by avoiding the target node IDs.
    buggyAsts = GenerateBuggies(
            ast_dict, lang_info, nodeIds, labels,
            skip_ids, function_names, user_n, total_nodes,
            nodetypes)

    asts = buggyAsts + nonBuggyAsts

    return asts

def GenerateNonBuggies(
        ast_dict: dict, lang_info: dict, nodeIds: set, labels: set,
        skip_ids: set, function_names: set, nodetypes: dict):
    """This function generated non-buggy program ASTs.

    args:
        ast_dict (dict): seed program's ast.
        lang_info (dict): C language specification information.
        nodeIds (set): set of target node IDs.
        labels (set): set of C program label names (e.g., LABEL L1).
        skip_ids (set): set of node ids to skip for analysis.
        function_names (set): set of function names declared in the source code.
        nodetypes (dict): node types that we handle and skip.

    returns:
        (list) list of newly generated ASTs.
    """

    # List of generated new ASTs.
    asts = [ast_dict]

    idx = 1
    for nodeId in nodeIds:
        dummy = [-1]
        for j in range(0, 2):
            ast_copy = copy.deepcopy(ast_dict)
            depth = Shared.astEditor(
                        ast_copy, nodeId, lang_info, 1, 
                        skip_ids, function_names,
                        nodetypes, labels, dummy)
            if ast_copy not in asts:
                asts.append(ast_copy)

    return asts[1:]

def GenerateBuggies(
        ast_dict: dict, lang_info: dict, nodeIds: set, labels: set,
        skip_ids: set, function_names: set, user_n: int, total_nodes: int,
        nodetypes: dict):
    """This function generated buggy program ASTs.

    args:
        ast_dict (dict): seed program's ast.
        lang_info (dict): C language specification information.
        nodeIds (set): set of target node IDs.
        labels (set): set of C program label names (e.g., LABEL L1).
        skip_ids (set): set of node ids to skip for analysis.
        function_names (set): set of function names declared in the source code.
        total_nodes (int): number of nodes in the AST.
        nodetypes (dict): node types that we handle and skip.

    returns:
        (list) list of newly generated ASTs.
    """


    # List of generated new ASTs.
    asts = [ast_dict]

    for i in range(1, user_n):
        if i in skip_ids:
            continue
        else:
            # For each run, select 5 random node IDs, which are not
            # one of nodes to skip or target, to edit.
            targetNodeIds = set()
            for i in range(0, 5):
                n = random.randint(0, total_nodes)
                while n in list(skip_ids)+list(nodeIds):
                    n = random.randint(0, total_nodes)
                targetNodeIds.add(n)

            ast_copy = copy.deepcopy(ast_dict)
            depth = Shared.astEditorForDirectedBuggies(
                        ast_copy, lang_info, 1, 
                        skip_ids, function_names,
                        nodetypes, labels, targetNodeIds)
            if ast_copy not in asts:
                asts.append(ast_copy)
    
    return asts[1:]
