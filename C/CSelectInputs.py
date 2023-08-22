import os, sys
import json
import argparse
import math
import subprocess
import copy

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
        controlled_iptDir: str):
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
            General.dumpToJson(f"./misc/alignmentWith_{fileId}.json", alignment)

            # Compute the similarity.
            simValue = Select.ComputeSimilarity(alignment, len(seedNodesList))

            astId2SimValue[fileId] = simValue

    # DEBUG
    General.dumpToJson("./misc/astId2SimValue.json", astId2SimValue)

    return

def GetNodesInStr(nodesList: list):
    """
    """
    
    nodesStrList = []

    for node in nodesList:
        nodesStrList.append(str(node))

    return nodesStrList
