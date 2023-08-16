import os, sys
import json
import argparse
import math
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import DPGen4JIT.C.CLearning as CLearning
import C.Shared as Shared

def SelectInputs(arguments: dict, binsPath: str, CFiles: set, controlled_iptDir):
    """
    """

    buggyIds, nonbuggyIds = CLearning.RunOracle(arguments, binsPath, CFiles, controlled_iptDir)
    print (f"DIRECTED: Buggy IDs: {buggyIds}")
    print (f"DIRECTED: NonBuggy IDs: {nonbuggyIds}")

    return
