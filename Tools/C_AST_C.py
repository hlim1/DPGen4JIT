import copy
import os, sys
import random
import argparse
import json

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import C.SourceToSource as C_S2S

HANDLED_NODETYPES = [
    'FuncDef', 'FileAST', 'FuncDecl', 'IdentifierType',
    'Constant', 'UnaryOp', 'BinaryOp', 'TypeDecl',
    'ext', 'body', 'Compound', 'Decl', 'init',
    'Return'
]

def argument_parser():
    """This function parses the passed argument.

    args:
        None

    returns:
        (str) file path.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-d",
            "--directory",
            type=str,
            required=True,
            help="A directory path where all C files are located."
    )
    args = parser.parse_args()

    return args.directory

def dumpToJson(filepath: str, target: dict):

    converted = json.dumps(target, indent=4)
    with open(filepath, "w") as f:
        f.write(converted)

def GetUnhandledNodeTypes(ast: dict, depth: int, unhandled: set):
    """This function traverse AST tree for the two tasks:
        (1) count the number of nodes.
        (2) 

    args:
        ast (dict): ast to scan.
        depth (int): tree depth.
        unhandled (set): set of _nodetypes that are not handled yet.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if key not in HANDLED_NODETYPES:
                        unhandled.add(key)
                    if value:
                        for elem in value:
                            depth = GetUnhandledNodeTypes(elem, depth, unhandled) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    if key not in HANDLED_NODETYPES:
                        unhandled.add(key)
                    depth = GetUnhandledNodeTypes(value, depth, unhandled) + 1
                else:
                    depth += 1
        else:
            depth += 1

    if '_nodetype' in ast and ast['_nodetype'] not in HANDLED_NODETYPES:
        unhandled.add(ast['_nodetype'])

    return depth

def GetAllNodeTypes(ast: dict, depth: int, nodeTypes: set):
    """This function traverse AST tree for the two tasks:
        (1) count the number of nodes.
        (2) 

    args:
        ast (dict): ast to scan.
        depth (int): tree depth.
        nodeTypes (set): set of all _nodetypes in the ast.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        nodeTypes.add(key)
                        for elem in value:
                            depth = GetAllNodeTypes(elem, depth, nodeTypes) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    nodeTypes.add(key)
                    depth = GetAllNodeTypes(value, depth, nodeTypes) + 1
                else:
                    depth += 1
        else:
            depth += 1

    if '_nodetype' in ast:
        nodeTypes.add(ast['_nodetype'])

    return depth


def main1(directory: str, info: dict):

    files = os.listdir(directory)
    
    nodeTypes = set()
    for f in files:
        if f.endswith('.c'):
            f_path = f"{directory}/{f}"
            print (f"Current File: {f_path}")
            try:
                # Convert C source code to python3 'dict' object.
                ast_dict = C_S2S.file_to_dict(f_path)
                depth = GetAllNodeTypes(ast_dict, 1, nodeTypes)
            except:
                print (f"|__Failed")
                info["fails"].append(f)

    info["nodetypes"] = list(copy.deepcopy(nodeTypes))
    
    return info

def main2(directory: str, info: dict):

    files = os.listdir(directory)
    
    unhandled = set()
    for f in files:
        if f.endswith('.c'):
            f_path = f"{directory}/{f}"
            if f not in info["fails"]:
                print (f"Current File: {f_path}")
                # Convert C source code to python3 'dict' object.
                ast_dict = C_S2S.file_to_dict(f_path)
                depth = GetUnhandledNodeTypes(ast_dict, 1, unhandled)
            else:
                print (f"Skip: {f_path}")

    info["unhandled"] = list(copy.deepcopy(unhandled))
    info["handled"] = list(copy.deepcopy(set(info["nodetypes"]) - unhandled))

    return info
            
if __name__ == "__main__":
    directory = argument_parser()

    info = {"fails":[], "nodetypes":[], "handled":[], "unhandled":[]}

    info = main1(directory, info)
    info = main2(directory, info)

    dumpToJson(f"./info.json", info)
