import os, sys
import json
import argparse
import math
import subprocess
import copy
import shutil

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import DPGen4JIT.C.CLearning as CLearning
import DPGen4JIT.C.Shared as Shared
import DPGen4JIT.Shared.SequenceAlignment as SEQAlign
import DPGen4JIT.Shared.General as General
import DPGen4JIT.Shared.SelectInputs as Select 

def SelectInputs(
        arguments: dict, seedAST: dict, binsPath: str, CFiles: set, 
        controlled_iptDir: str, root: str, seed: str, user_n: int):
    """
    """

    # Classify the newly generated programs into buggy or non-buggy programs.
    buggyIds, nonbuggyIds = CLearning.RunOracle(arguments, binsPath, CFiles, controlled_iptDir)
    print (f"DIRECTED: Buggy IDs: {buggyIds}")
    print (f"DIRECTED: NonBuggy IDs: {nonbuggyIds}")
    
    # Get node IDs to actual node objects.
    nodeId2Node = {}
    nodeId = Shared.assignIdsToNodes(seedAST, 1, nodeId2Node)
    
    # Extract node objects and convert them into a list that maintains the order of node IDs.
    seedNodesList = copy.deepcopy(GetNodesInStr(list(nodeId2Node.values())))

    # Get the list of AST files.
    ASTFiles = os.listdir(f"{controlled_iptDir}/asts")

    astId2SimValue = {}

    for ASTFile in ASTFiles:
        fileId = int((ASTFile.split('__')[-1]).split('.')[0])
        # For all AST files that were generated into an actual code and classified,
        # compute the similarities with the seed AST.
        if fileId in buggyIds or fileId in nonbuggyIds:
            ast = General.loadJson(f"{controlled_iptDir}/asts/{ASTFile}")
            # Get node IDs to actual node objects.
            nodeId2Node = {}
            nodeId = Shared.assignIdsToNodes(ast, 1, nodeId2Node)
            nodes = copy.deepcopy(list(nodeId2Node.values()))
            nodesList = copy.deepcopy(GetNodesInStr(nodes))
            seedCopy = copy.deepcopy(seedNodesList)
            # Compute the nodes alignment between the seed and the new AST.
            alignment = SEQAlign.SequenceAlignment(seedCopy, nodesList)
            General.dumpToJson(f"{root}/misc/alignmentWith_{fileId}.json", alignment)

            # Compute the similarity.
            simValue = Select.ComputeSimilarity(alignment, len(seedNodesList))

            astId2SimValue[fileId] = simValue

    selectedIds = SelectIDs(astId2SimValue, buggyIds, nonbuggyIds, user_n)

    selectedBuggyIds = set()
    selectedNonBuggyIds = set()
    
    final_iptDir = f"{root}/inputs"
    files = os.listdir(controlled_iptDir)
    for f in files:
        if f.endswith('.c'):
            fileId = int((f.split('__')[-1]).split('.')[0])
            if fileId in selectedIds:
                src_path = f"{controlled_iptDir}/{f}"
                dst_path = f"{final_iptDir}/{f}"
                shutil.move(src_path, dst_path)

                if fileId in buggyIds:
                    selectedBuggyIds.add(fileId)
                else:
                    selectedNonBuggyIds.add(fileId)

    subprocess.run(['cp', seed, f"{final_iptDir}/poc_original__0.c"])

    # DEBUG
    General.dumpToJson(f"{root}/misc/astId2SimValue.json", astId2SimValue)

    return selectedBuggyIds, selectedNonBuggyIds

def SelectIDs(astId2SimValue: dict, buggyIds: set, nonbuggyIds: set, user_n: int):
    """
    """

    selectedBuggyIds = [0]
    selectedNonBuggyIds = []

    _astId2SimValue = SortDictByValues(astId2SimValue)

    mid = user_n/2

    buggies_ctn = 1
    nonbuggies_ctn = 0

    for astId in _astId2SimValue:
        if astId in buggyIds and buggies_ctn < mid:
            selectedBuggyIds.append(astId)
            buggies_ctn += 1
        elif astId in nonbuggyIds and nonbuggies_ctn < mid:
            selectedNonBuggyIds.append(astId)
            nonbuggies_ctn += 1

    selectedIds = selectedBuggyIds + selectedNonBuggyIds

    return selectedIds

def GetNodesInStr(nodesList: list):
    """
    """
    
    nodesStrList = []

    for node in nodesList:
        nodesStrList.append(str(node))

    return nodesStrList

def SortDictByKey(dictTosort: dict):
    """This function sorts dictionary by keys in ascending order.

    args:
        dictToSort (dict): dictionary to sort.

    returns:
        (dict) sorted dictionary.
    """

    keysOnly = list(dictTosort.keys())
    keysOnly.sort()
    sorted_dict = {i:dictTosort[i] for i in keysOnly}

    return sorted_dict

def SortDictByValues(dictToSort: dict):
    """This function sorts dictionary by values in descending order.

    args:
        dictToSort (dict): dictionary to sort.

    returns:
        (dict) sorted dictionary.
    """

    sorted_dict = sorted(
            dictToSort.items(), key=lambda x:x[1], reverse=True)

    return dict(sorted_dict)
