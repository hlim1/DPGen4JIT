"""
  This program generates a modified PoC that is one different from the original PoC.

  Phase-1: Initial Random Variant Code Generation Phase.

  Author: Anonymous.
"""

import os, sys
import json
import copy
import random
import subprocess
import argparse
from random import randint

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import JavaScript.JSAstGenerator as JSAstG
import JavaScript.SharedEditors as Shared

def RandomVariantGenerator(
        variantsPath: str, astDirPath: str, fileBase: str, originalJS: str, number: int,
        langInfo: dict
):
    """This function calls ast_editor specified N times to modify
    the original input program's ast and generate variant input programs.

    args:
        variantsPath (str): directory where all variants will be stored.
        fileBase (str): name of the original input file without the extension.
        originalJS (str): original JS code to generate variants from.
        number (int): user-specified number to generate N number of variants.
        langInfo (dict): information about the JS language, such as types and methods, etc.

    returns:
        (dict) keep a map between the variant id-to-edited node id.
    """

    astFilePaths = []
    astId2editNodeId = {}
    
    # Generate AST for the original JS code.
    # G = (V, E).
    originalAST = JSAstG.AstGenerator(originalJS)

    # Generate AST variants and store them to the astDirPath.
    astVariants = randomASTVariantGenerator(originalAST.toDict(), number, langInfo)

    for variantId, astVariant in astVariants.items():
        variantFilePath = f"{astDirPath}/{fileBase}-variant__{variantId}.json"
        astFilePaths.append(variantFilePath)
        with open(variantFilePath, 'w') as ast_f:
            json.dump(astVariant[0], ast_f)
        astId2editNodeId[variantId] = astVariant[1]
        variantId += 1

    # Generate JS code variants based on the generated AST variants.
    Shared.JSCodeGenerator(variantsPath, astFilePaths)

    return originalAST.toDict(), astId2editNodeId

def randomASTVariantGenerator(originalAST: dict, number: int, langInfo: dict):
    """This function edits the original AST to generate N number of AST variants.

    args:
        originalAST (dict): abstract syntax tree of the original input code.
        number (int): user-specified number to generate N number of variants.
        langInfo (dict): information about the JS language, such as types and methods, etc.

    returns:
        (dict) dictionary of ast variant-to-edited target node id.
    """

    # Lists to hold the generated variants.
    astVariants_ref = [originalAST]
    astVariants = {}
    # True if needing the target node id.
    need_target = True

    # Scans the tree once to find the total number of nodes
    # in the tree.
    total_nodes = Shared.treeScanner(originalAST, 1)

    # Tracks the number of generated variants number.
    generated = 1
    # Sets the target_node_id to 1.
    target_node_id = 1

    # Tracks the edited node id to edited info.
    id2edit = {}
  
    # Call ast_editor function to modify the original input program's AST.
    for i in range(1, total_nodes*2):
        if generated == number*2:
            break
        else:
            ast_copy = copy.deepcopy(originalAST)
            # Edit AST tree until actually one node was edited. The editing can fail if
            # the node type is currently not handle, which then the WARNING will be printed.
            # If such case happen, then we want to choose another node to edit without incrementing i.
            while need_target:
                # Randomly select the node id between 1..N-1, where N = |V|.
                #target_node_id = randint(1, total_nodes - 1)
                need_target = Shared.ast_editor(ast_copy, target_node_id, langInfo, id2edit)
                if target_node_id >= total_nodes:
                    target_node_id = 1
                else:
                    # Either a new ast variant was generated or not, we increment the target_node_id
                    # to point to the next node.
                    target_node_id += 1

            # IF the editing was successful, need_target will be set to False.
            # Thus, we need to manually set to True, to the main for-loop continues.
            need_target = True
            # If the variant does not already exist in the astVariants list, add to it.
            if ast_copy not in astVariants_ref:
                astVariants_ref.append(ast_copy)
                astVariants[generated] = [ast_copy, target_node_id-1]
                generated += 1

            if target_node_id > total_nodes:
                target_node_id = 1

    return astVariants

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="JavaScript file to generate variants from."
    )
    args = parser.parse_args()

    return args.file

if __name__ == "__main__":
    jsFilePath = argument_parser()

    number = 1

    langInfo = {}
    currentdir = os.path.dirname(os.path.realpath(__file__))
    with open(f"{currentdir}/JSLanguage.json") as langFile:
        langInfo = json.load(langFile)

    with open(jsFilePath) as jsFile:
        jsCode = jsFile.read()
        originalAST = JSAstG.AstGenerator(jsCode)
        print ("Original AST: ", originalAST.toDict())

        # Generate AST variants and store them to the astDirPath.
        astVariants = randomASTVariantGenerator(originalAST.toDict(), number, langInfo)

        for id, ast in astVariants.items():
            print ("Modified AST: ", id, ast)
