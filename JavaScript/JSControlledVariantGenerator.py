"""
  This program generates a PoC variants based on the result from the Learning phase.

  Phase-3: Variant Generation Based on Learning Phase.

  Author: Anonymous.
"""

import os, sys
import json
import copy
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import JavaScript.JSAstGenerator as JSAstG
import JavaScript.SharedEditors as Shared
import JavaScript.JSVariantLearning as JSVariantLearning

def GenerateInputs(
        rootPath: str, user_n: int, targetNodeIds: list, fileBase: str, seed_ast: dict,
        language_info: dict, jitOnCommand: list, jitOffCommand: list):
    """
    """

    astFilePaths = []

    astVariants = controlledASTVariantGenerator(
                        seed_ast, user_n, 
                        language_info, targetNodeIds,
                        rootPath, jitOnCommand, 
                        jitOffCommand)

    variantId = 1
    for astVariant in astVariants:
        variantFilePath = f"{rootPath}/inputs/asts/{fileBase}-variant__{variantId}.json"
        astFilePaths.append(variantFilePath)
        with open(variantFilePath, 'w') as ast_f:
            json.dump(astVariant, ast_f)
        variantId += 1

    # Generate JS code variants based on the generated AST variants.
    Shared.JSCodeGenerator(f"{rootPath}/inputs", astFilePaths)

    return variantId

def GenerateBuggies(
        rootPath: str, user_n: int, targetNodeIds: list, fileBase: str, seed_ast: dict,
        language_info: dict, jitOnCommand: list, jitOffCommand: list, last_ipt_id: int):
    """

    args:
        rootPath (str): root directory path.
        user_n (int): user-specified number to generate N number of variants.
        targetNodeIds (list): list of target node ids to edit.
        fileBase (str): name of the original input file without the extension.
        seed_ast (dict): AST of the original input program.
        language_info (dict): information about the JS language, such as types and methods, etc.
        jitOnCommand (list): command to execute VM with jit compilation on.
        jitOffCommand (list): command to execute VM with jit compilation off.
        last_ipt_id (int): lastly generated input id.

    returns:
        None.
    """

    astVariants = []

    generated = 0
    for i in range(1, 1001):
        if generated == user_n:
            break
        else:
            ast_copy = copy.deepcopy(seed_ast)
            is_loop_edit = [False]
            dummy = Shared.treeModifier2(
                        ast_copy, 1, targetNodeIds, language_info, is_loop_edit,
                        jitOnCommand, jitOffCommand)
            is_buggy = checkGenerated(ast_copy, rootPath, jitOnCommand, jitOffCommand)

        if (
                ast_copy != seed_ast and 
                ast_copy not in astVariants
                and is_buggy
        ):
            astVariants.append(ast_copy)
            generated += 1

    astFilePaths = []
    ipt_id = last_ipt_id
    for ast in astVariants:
        variantFilePath = f"{rootPath}/inputs/asts/{fileBase}-variant__{ipt_id}.json"
        astFilePaths.append(variantFilePath)
        with open(variantFilePath, 'w') as ast_f:
            json.dump(ast, ast_f)
        ipt_id += 1

    # Generate JS code variants based on the generated AST variants.
    Shared.JSCodeGenerator(f"{rootPath}/inputs", astFilePaths)

def ControlledVariantGenerator(
        rootPath: str, inputsPath: str, astDirPath: str, fileBase: str, originalAST: dict, 
        number: int, langInfo: dict, targetNodeIds: list, jitOnCommand: list, jitOffCommand: list
):
    """This function calls ast_editor specified N times to edit the copy of original 
    input program's AST based on the result from the Learning phase. In other words, 
    this function targets only some number of specific AST nodes.

    args:
        rootPath (str): root directory path.
        inputsPath (str): directory where all input variants will be stored.
        astDirPath (str): directory where all asts will be stored.
        fileBase (str): name of the original input file without the extension.
        originalAST (dict): AST of the original input program.
        number (int): user-specified number to generate N number of variants.
        langInfo (dict): information about the JS language, such as types and methods, etc.
        targetNodeIds (list): list of target node ids to edit.
        jitOnCommand (list): command to execute VM with jit compilation on.
        jitOffCommand (list): command to execute VM with jit compilation off.

    returns:
        None.
    """

    astFilePaths = []

    astVariants = controlledASTVariantGenerator(
                    originalAST, number, langInfo, targetNodeIds,
                    rootPath, jitOnCommand, jitOffCommand)

    variantId = 1
    for astVariant in astVariants:
        variantFilePath = f"{astDirPath}/{fileBase}-variant__{variantId}.json"
        astFilePaths.append(variantFilePath)
        with open(variantFilePath, 'w') as ast_f:
            json.dump(astVariant, ast_f)
        variantId += 1

    # Generate JS code variants based on the generated AST variants.
    Shared.JSCodeGenerator(inputsPath, astFilePaths)

    return variantId

def controlledASTVariantGenerator(
        originalAST: dict, number: int, langInfo: dict, targetNodeIds: list, 
        rootPath: str, jitOnCommand: list, jitOffCommand: list):
    """This function make a copy of the original AST and edits the target node.

    args:
        originalAST (dict): AST of the original input program.
        number (int): user-specified number to generate N number of variants.
        langInfo (dict): information about the JS language, such as types and methods, etc.
        targetNodeIds (list): list of target node ids to edit.
        rootPath (str): root directory path.

    returns:
        (list) list of AST variants.
    """

    astVariants = []

    generated = 1

    id2edit = {}

    flag = True
    targetNodeIds_idx = [0]
    for i in range(1, 1001):
        if generated == number*2:
            break
        else:
            ast_copy = copy.deepcopy(originalAST)
            target_node_id = getTargetNodeId(targetNodeIds, targetNodeIds_idx)

            if flag:
                # Since we are sharing the ast_editor function, which returns 
                # a boolean value to indicate whether we need a new target id 
                # or not used in the random AST editor (Phase-1) but not in this 
                # controlled AST editor, we just add a place holder, dummy, to receive the value.
                # This dummy is not being used in anywhere.
                dummy = Shared.ast_editor(ast_copy, target_node_id, langInfo, id2edit)
                is_buggy = checkGenerated(ast_copy, rootPath, jitOnCommand, jitOffCommand)
                flag = False
            else:
                is_loop_edit = [False]
                dummy = Shared.treeModifier2(
                            ast_copy, 1, targetNodeIds, langInfo, is_loop_edit,
                            jitOnCommand, jitOffCommand)
                is_buggy = checkGenerated(ast_copy, rootPath, jitOnCommand, jitOffCommand)
                flag = True

            if (ast_copy != originalAST and ast_copy not in astVariants):
                if ((not flag and not is_buggy) or (flag and is_buggy)):
                    astVariants.append(ast_copy)
                    generated += 1

    return astVariants

def getTargetNodeId(targetNodeIds: list, targetNodeIds_idx: list):
    """This function returns the target node id for the editor to target.

    args:
        targetNodeIds (list): list of target node ids to edit.
        targetNodeIds_idx (list): list of target node id indices.

    returns:
        (int) target ast node id.
    """
    
    if targetNodeIds_idx[0] >= len(targetNodeIds):
        targetNodeIds_idx[0] = 0

    target_id = targetNodeIds[targetNodeIds_idx[0]]
    targetNodeIds_idx[0] += 1

    return target_id

def checkGenerated(ast_copy: dict, rootPath: str, jitOnCommand: list, jitOffCommand: list):
    """
    """

    temporary_ast_path = f"{rootPath}/misc/ctr_ast_temp.json"
    with open(temporary_ast_path, 'w') as ast_f:
        json.dump(ast_copy, ast_f)
    temporary_js_path = f"{rootPath}/misc/ctr_js_temp.js"

    Shared.SingleJSCodeGenerator(temporary_ast_path, temporary_js_path)

    jitOnCommand[-1] = temporary_js_path
    jitOffCommand[-1] = temporary_js_path

    jitOnOut = JSVariantLearning.RunJITExe(jitOnCommand)
    jitOffOut = JSVariantLearning.RunJITExe(jitOffCommand)

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

    return is_buggy
