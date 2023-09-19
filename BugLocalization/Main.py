import os, sys
import json
import argparse
import copy
import subprocess

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import Shared.General as General

import CollectCov
import Oracle
import Ochiai

def BugLocalization(buggyIds: set, nonbuggyIds: set, coveragePath: str):
    """
    """

    allIds = buggyIds.union(nonbuggyIds)

    buggies = []
    nonbuggies = []

    base = set()

    for fId in allIds:
        dirPath = f"{coveragePath}/{fId}/jsons"
        if os.path.exists(dirPath):
            fullData = {}
            if not os.path.exists(f"{coveragePath}/{fId}/jsons/full.json"):
                files = os.listdir(dirPath)
                for f in files:
                    data = General.loadJson(f"{dirPath}/{f}")
                    fullData |= data
                General.dumpToJson(f"{coveragePath}/{fId}/jsons/full.json", fullData)
            else:
                fullData = General.loadJson(f"{coveragePath}/{fId}/jsons/full.json")

            if fId in buggyIds:
                if fId == 0:
                    base = copy.deepcopy(set(fullData.keys()))
                else:
                    buggies.append(copy.deepcopy(set(fullData.keys())))
            else:
                nonbuggies.append(copy.deepcopy(set(fullData.keys())))

    (
        entityId2suspicious,
        entityId2statement
    ) = Ochiai.Ochiai(base, buggies, nonbuggies)
    
    stmt2sus = {}
    for entityId, suspicious in entityId2suspicious.items():
        statement = entityId2statement[entityId]
        stmt2sus[statement] = suspicious

    stmt2sus = General.SortDictByValues(stmt2sus)

    return stmt2sus

def RankStmts(stmt2sus: dict):
    """
    """

    rank2stmts = {}

    rank = 0
    curSus = -1;
    for stmt, sus in stmt2sus.items():
        if curSus != sus:
            curSus = sus
            rank += 1
            rank2stmts[rank] = [stmt]
        else:
            rank2stmts[rank].append(stmt)

    return rank2stmts

def mapToFiles(rank2stmts: dict, coveragePath: str):
    """
    """

    baseJSONSPath = f"{coveragePath}/0/jsons"
    assert (
        os.path.exists(baseJSONSPath)
    ), f"ERROR: baseJSONSPath {baseJSONSPath} does not exist."
    baseJSONFiles = os.listdir(baseJSONSPath)

    r2rank = {}
    rank = 1
    file2rank = {}
    for JSONFile in baseJSONFiles:
        filePath = f"{baseJSONSPath}/{JSONFile}"
        stmt2count = General.loadJson(filePath)
        for r, stmts in rank2stmts.items():
            for stmt in stmts:
                if stmt in stmt2count:
                    if JSONFile not in file2rank:
                        if r not in r2rank:
                            r2rank[r] = rank
                            rank += 1
                        file2rank[JSONFile] = r2rank[r]

    return file2rank

def GetCFilePaths(dirPath: str):
    """
    """

    paths = set()

    cfiles = os.listdir(dirPath)

    for cfile in cfiles:
        if cfile.endswith('c'):
            paths.add(f"{dirPath}/{cfile}")

    return paths

def StoreOrgGcnoFiles(allPaths2gcnoTXT: str, allPaths2gcdaTXT: str):
    """
    """

    compilerRoot = '/'.join(allPaths2gcnoTXT.split('/')[0:-1])
    gcnosDir = f"{compilerRoot}/gcnos"

    if not os.path.exists(gcnosDir):
        os.makedirs(gcnosDir)

    allPaths2gcno = General.loadTxtFile(allPaths2gcnoTXT)

    copy2org_path = {}

    for gcnoPath in allPaths2gcno:
        filename = (gcnoPath.split('/')[-1]).strip()
        copyPath = f"{gcnosDir}/{filename}"
        if not os.path.exists(copyPath):
            print (f"COPYING ORIGINAL GCNO FILE: {gcnoPath.strip()}")
            subprocess.run(["cp", gcnoPath.strip(), copyPath])

        copy2org_path[copyPath] = gcnoPath.strip()

    allPaths2gcda = General.loadTxtFile(allPaths2gcdaTXT)
    for gcdaPath in allPaths2gcda:
        if os.path.exists(gcdaPath.strip()):
            #print (f"REMOVING GCDA FILE: {gcdaPath.strip()}")
            subprocess.run(["rm", gcdaPath.strip()])

    return allPaths2gcno, copy2org_path, allPaths2gcda

def CopyBins(binsPath: str, destPath: str, CFiles: list, arguments: dict):
    """
    """

    fileIds = []
    for CFile in CFiles:
        if CFile.endswith('.c'):
            fileId = int(CFile.split('__')[-1].split('.')[0])
            fileIds.append(fileId)

    bins = os.listdir(binsPath)

    for binfile in bins:
        fileId = int(binfile.split('__')[-1])
        if fileId in fileIds:
            binPath = f"{binsPath}/{binfile}"
            subprocess.run(["cp", binPath, f"{destPath}/{binfile}"])

    command = [arguments['for_testing']]
    command.extend(arguments['arguments'])
    command.append(arguments['seed'])
    command.append("-o")
    command.append(f"{destPath}/clang_bin__0")

    subprocess.run(command)

def argument_parser():
    """This function parses the passed argument.

    args:
        None

    returns:
        (str) file path.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="Command-line arugments file."
    )
    args = parser.parse_args()

    return args.file

def main(arguments: dict):
    inputsPath = f"{arguments['root']}/inputs"
    binsPath = f"{arguments['root']}/inputs/bins"
    if not os.path.exists(binsPath):
        os.makedirs(binsPath)
    coveragePath = f"{arguments['root']}/coverages"

    allPaths2gcnoTXT = arguments['allPaths2gcno']
    allPaths2gcdaTXT = arguments['allPaths2gcda']
    (
        allPaths2gcno, 
        copy2org_path,
        allPaths2gcda
    ) = StoreOrgGcnoFiles(allPaths2gcnoTXT, allPaths2gcdaTXT)

    CFiles = GetCFilePaths(inputsPath)
    CopyBins(f"{arguments['root']}/controlled/bins", binsPath, CFiles, arguments)

    #CollectCov.CollectCoverage(
    #        arguments, allPaths2gcno, copy2org_path, CFiles, binsPath, 
    #        coveragePath, "clang")

    # Classify the newly generated programs into buggy or non-buggy programs.
    buggyIds, nonbuggyIds = Oracle.RunOracle(arguments, binsPath, CFiles, inputsPath)
    print (f"INPUTS: Buggy IDs: {buggyIds}")
    print (f"INPUTS: NonBuggy IDs: {nonbuggyIds}")
    
    CollectCov.CollectCoverage_WithDiffOPT(
            arguments, allPaths2gcno, copy2org_path, CFiles, binsPath, 
            coveragePath, "clang", buggyIds, nonbuggyIds, allPaths2gcda)

    stmt2sus = BugLocalization(buggyIds, nonbuggyIds, coveragePath)

    General.dumpToJson(f"{arguments['root']}/stmt2suspicious.json", stmt2sus)

    stmt2sus = General.loadJson(f"{arguments['root']}/stmt2suspicious.json")

    rank2stmts = RankStmts(stmt2sus)
    file2rank = mapToFiles(rank2stmts, coveragePath)

    file2rank = General.SortDictByValues(file2rank, False)

    General.dumpToJson(f"{arguments['root']}/file2rank.json", file2rank)

    rank2count = {}
    for filename, rank in file2rank.items():
        if rank not in rank2count:
            rank2count[rank] = 1
        else:
            rank2count[rank] +=1
    for rank, count in rank2count.items():
        print (f"rank = count: {rank} = {count}")

if __name__ == "__main__":
    argumentsJSON = argument_parser()
    arguments = General.loadJson(argumentsJSON)

    main(arguments)
