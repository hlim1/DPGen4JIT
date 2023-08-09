import json
import copy
import os, sys

def CRandomGenerator(ast_dict: dict, lang_info: dict, user_n: int):
    """
    """

    total_nodes = treeScanner(ast_dict, 1)

    # Tracks the number of generated variants number.
    generated = 1
    # Sets the target_node_id to 1.
    target_node_id = 1

    id2edit = {}

    asts = []

    # Call ast_editor function to modify the original 
    # input program's AST.
    for i in range(1, total_nodes*2):
        if generated == user_n*2:
            break
        else:
            ast_copy = copy.deepcopy(ast_dict)
            depth = ast_editor(
                        ast_copy, 38, lang_info, id2edit, 1)
            asts.append(ast_copy)
            # DEBUG
            break

    return asts

def treeScanner(ast: dict, depth: int):

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                #print (f"{key} = {value}")
                if isinstance(value, list):
                    for elem in value:
                        depth = treeScanner(elem, depth) + 1
                elif isinstance(value, dict):
                    depth = treeScanner(value, depth) + 1
                else:
                    depth += 1

    return depth

def ast_editor(
        ast: dict, target_node_id: int, lang_info: dict,
        id2edit: dict, depth: int):
    """
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        for elem in value:
                            depth = ast_editor(elem, target_node_id, 
                                    lang_info, id2edit, depth) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    depth = ast_editor(value, target_node_id, 
                            lang_info, id2edit, depth) + 1
                else:
                    edit_dict(ast, key)
                    depth += 1
        else:
            depth += 1

    return depth

def edit_dict(node: dict, key: str):
    """
    """

    if key == 'value' and node[key] == str(123):
        node['value'] = str(321)
