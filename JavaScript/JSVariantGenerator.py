"""
    This program holds a function that is like a main function, which calls
    all other phase functions in the pipeline to generate PoC code variants.

    Author: Terrence Lim.
"""

import os, sys
import json
import copy
import random
import subprocess

from random import seed
from random import randint

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import JSRandomVariantGenerator as JSRandomVariantGenerator
import JSVariantLearning as JSVariantLearning
import JSControlledVariantGenerator as JSControlledVariantGenerator

JSLanguagePath = f"{currentdir}/JSLanguage.json"

def JSVariantGenerator(paths: dict, orgJSCode: str, arguments: dict, maxVars: int):
    """This function calls 3 functions for each phase to somewhat cleverly
    generate the input variants. In the main pipeline, simply call this function.

    args:
        paths (dict): paths information.
        orgJSPath (str): path of original JS file.
        orgJSCode (str): original JS code in string.
        arguments (dict): arguments information.
        maxVars (int): maximum number of variants, which the user wants to generate.

    returns:
        None.
    """

    events = ""

    orgJSPath = arguments["inputPath"]

    langInfo = None
    with open(JSLanguagePath) as langFile:
        langInfo = json.load(langFile)

    assert (
            langInfo != None
    ), f"ERROR: langInfo is empty."

    # Extract paths from the 'paths' dict.
    rVariantsPath  = paths["random"]
    rASTDirPath    = paths["random-asts"]
    rootPath       = paths["root"]
    rootASTDirPath = paths["root-asts"]
    inputsPath     = f"{rootPath}/inputs"
    
    # Split original input file's base and the extension.
    inputFileBase, ext = os.path.splitext(os.path.basename(orgJSPath))

    # Phase-1: Initial Random Variant Code Generation Phase.
    print ("Phase-1: PoC Random Variant Generation.")
    events += "Phase-1: PoC Random Variant Generation.\n"
    (
        originalAST,
        variantId2editNodeId
    ) = JSRandomVariantGenerator.RandomVariantGenerator(
                                            rVariantsPath, rASTDirPath, inputFileBase,
                                            orgJSCode, maxVars, langInfo)
    # Phase-2: Learning Phase.
    print ("Phase-2: Learning Phase.")
    events += "Phase-2: Learning Phase.\n"
    (
        targetASTNodeIds,
        buggyVariantIDs,
        jitOnCommand,
        jitOffCommand
    ) = JSVariantLearning.Learning(rVariantsPath, arguments, variantId2editNodeId)

    assert (len(targetASTNodeIds) > 0), f"ERROR: No target node Ids."

    # Phase 3: Variant Generation Based on Learning Phase.
    print ("Phase-3: PoC Controlled Variant Generation.")
    events += "Phase-3: PoC Controlled Variant Generation.\n"
    lastVarId = JSControlledVariantGenerator.ControlledVariantGenerator(
                    rootPath, inputsPath, rootASTDirPath, inputFileBase, originalAST,
                    maxVars, langInfo, targetASTNodeIds, jitOnCommand, jitOffCommand)

    # Code to move all bug triggering variant code files to the root.
    if len(buggyVariantIDs) > 0:
        rVariants = os.listdir(rVariantsPath)
        for variant in rVariants:
            if ".js" in variant:
                variantId = int(variant.split('__')[1].split('.')[0])
                if variantId in buggyVariantIDs:
                    inputsFilePath = f"{inputsPath}/{inputFileBase}-variant__{lastVarId}.js"
                    subprocess.run(['mv',f"{rVariantsPath}/{variant}", inputsFilePath])
                    lastVarId += 1

    return events
