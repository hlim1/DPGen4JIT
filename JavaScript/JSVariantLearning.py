"""
    This file holds code for Phase-2: Learning Phase.

    Author: Anonymous.
"""

import os, sys
import subprocess

JSEXT = ".js"

def Learning(variantsPath: str, exeCommands: dict, variantId2editNodeId: dict):
    """This function runs variants twice - once with the JIT compilation on
    and once without - then select the node ids to edit in the next phase.

    args:
        variantsPath (str): directory where all variants are stored.
        exeCommands (map): commands to execute the JIT compiler.
        variantId2editNodeId (map): a map between the variant id-to-edited node id.

    returns:
        (list) set of node ids to edit.
    """
    
    # Prepare command for executing JIT system with a JIT compilation on.
    jitOnCommand = [exeCommands["jitExePath"]]
    jitOnCommand.extend(exeCommands["jitArguments"])
    jitOnCommand.append(None)
    
    # Prepare command for executing JIT system with a JIT compilation off.
    jitOffCommand = [exeCommands["jitExePath"], exeCommands["jitOff"]]
    jitOffCommand.append(None)

    # Get the list of files under variants directory.
    variants = os.listdir(variantsPath)

    # List (set) of node ids to edit in the next phase.
    targetASTNodeIds = []

    # Track random variant ID that triggers bug in JIT.
    buggyVariantIDs = []

    for variant in variants:
        if variant.endswith(JSEXT):
            variantId = int(variant.split('__')[1].split('.')[0])

            # Update the last element with the variant file path.
            jitOnCommand[-1] = f"{variantsPath}/{variant}"
            jitOffCommand[-1] = f"{variantsPath}/{variant}"

            # Run variant twice.
            jitOnOut = RunJITExe(jitOnCommand)
            jitOffOut = RunJITExe(jitOffCommand)

            # Analyze the results and get a set of target AST node IDs.
            is_buggy = ResultAnalyzer(variantId, jitOnOut, jitOffOut, variantId2editNodeId, targetASTNodeIds)

            if is_buggy:
                buggyVariantIDs.append(variantId)

    return targetASTNodeIds, buggyVariantIDs, jitOnCommand, jitOffCommand


def RunJITExe(commands: list):
    """This function runs the variant with the passed command under subprocess
    and returns the output result.

    args:
        commands (list): command for executing JIT system.

    returns:
    
    """

    output = subprocess.run(commands, capture_output=True, text=True)

    return output

def ResultAnalyzer(
        variantId: int, jitOnOut, jitOffOut, 
        variantId2editNodeId: dict, targetASTNodeIds: list
):
    """This function analyzes the output results and identify the node ids to target for edit.

    args:
        variantId (int): currently analyzing variant's ID.
        jitOnOut (str): standard output from the execution with JIT compilation on.
        jitOffOut (str): standard output from the execution without JIT compilation.
        variantId2editNodeId (dict): a map between the variant id-to-edited node id.
        targetASTNodeIds (list): list (set) of target AST node ids to edit.

    returns:
        None
    """

    is_buggy = True

    # If jitOnOut is equal to jitOffOut, the variant does not trigger bug in the JIT.
    if str(jitOnOut.returncode) == '0' and jitOnOut.stdout == jitOffOut.stdout:
        astNodeId = variantId2editNodeId[variantId]
        if astNodeId not in targetASTNodeIds:
            targetASTNodeIds.append(astNodeId)
        is_buggy = False
    # jitOnOut == jitOffOut, which is empty output, if error occurs.
    elif str(jitOnOut.returncode) != '0' and jitOnOut.stdout == jitOffOut.stdout:
        is_buggy = False

    return is_buggy
