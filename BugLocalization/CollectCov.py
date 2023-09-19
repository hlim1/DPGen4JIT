import os, sys
import subprocess
import copy
import shutil

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import Shared.General as General
import Oracle

GCOV7 = "/usr/bin/gcov-7"
GCOV8 = "/usr/bin/gcov-8"

def CollectCoverage(
        arguments: dict, allPaths2gcno: list, copy2org_path: dict, 
        CFiles: set, binsPath: str, coveragePath: str, compiler: str):
    """
    """

    #subprocess.run(["rm", "-r", f"{binsPath}"])
    #os.makedirs(binsPath)

    commands = [arguments["compilerPath"]]
    commands.extend(arguments["arguments"])

    stderrs = ""

    for cfile in CFiles:
        if cfile.endswith('.c'):
            fileId = (cfile.split('__')[-1]).split('.')[0]
            dirPath = f"{coveragePath}/{fileId}"
            if os.path.exists(f"{dirPath}/jsons/full.json"):
                continue
            print (f"COMPILING: {cfile}")

            CopyGcnoFiles(copy2org_path)

            cmdCopy = copy.deepcopy(commands)
            binPath, output = Oracle.GenerateBin(cfile, binsPath, cmdCopy, compiler)

            if output.stderr and "error" in output.stderr:
                stderrs += f"{output.stderr}\n"
            else:
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath)
                try:
                    binOut = subprocess.run([binPath], capture_output=True, text=True, timeout=10)
                except subprocess.TimeoutExpired:
                    print (f"TIMEOUT: {binPath}")
                    continue

                allPaths2gcovs = CollectGcov(allPaths2gcno, dirPath)
                
                currentDir = os.getcwd()
                files = os.listdir(currentDir)
                for f in files:
                    if f.endswith(".gcov"):
                        fromfile = f"{currentDir}/{f}"
                        tofile = f"{dirPath}/{f}"
                        shutil.move(fromfile, tofile)

                ProcessGcov(allPaths2gcovs, dirPath)

    if "root" in arguments:
        root = arguments["root"]
    else:
        root = arguments["dirPath"]

    with open(f"{root}/misc/compileErrs.txt", "w") as f:
        f.write(stderrs)

    return

def CollectCoverage_WithDiffOPT(
        arguments: dict, allPaths2gcno: list, copy2org_path: dict, CFiles: set,
        binsPath: str, coveragePath: str, compiler: str, buggyIds: set, nonbuggyIds: set,
        allPaths2gcda: list):
    """
    """

    #subprocess.run(["rm", "-r", f"{binsPath}"])
    #os.makedirs(binsPath)

    commands = [arguments["compilerPath"]]
    # commands.extend(arguments["arguments"])

    stderrs = ""

    for cfile in CFiles:
        if cfile.endswith('.c'):
            fileId = (cfile.split('__')[-1]).split('.')[0]
            dirPath = f"{coveragePath}/{fileId}"
            if os.path.exists(f"{dirPath}/jsons/full.json"):
                continue
            print (f"COMPILING: {cfile}")

            CopyGcnoFiles(copy2org_path)
            for gcdaPath in allPaths2gcda:
                if os.path.exists(gcdaPath.strip()):
                    # print (f"REMOVING GCDA FILE: {gcdaPath.strip()}")
                    subprocess.run(["rm", gcdaPath.strip()])

            cmdCopy = copy.deepcopy(commands)
            if int(fileId) in buggyIds:
                cmdCopy.extend(arguments["arguments"])
            else:
                cmdCopy.extend(arguments["arguments4NonBuggy"])

            print (f"Command: {cmdCopy} for fileId: {fileId}")

            binPath, output = Oracle.GenerateBin(cfile, binsPath, cmdCopy, compiler)

            if output.stderr and "error" in output.stderr:
                stderrs += f"{output.stderr}\n"
            else:
                if not os.path.exists(dirPath):
                    os.makedirs(dirPath)
                binOut = subprocess.run([binPath], capture_output=True, text=True)
                allPaths2gcovs = CollectGcov(allPaths2gcno, dirPath)
                
                currentDir = os.getcwd()
                files = os.listdir(currentDir)
                for f in files:
                    if f.endswith(".gcov"):
                        fromfile = f"{currentDir}/{f}"
                        tofile = f"{dirPath}/{f}"
                        shutil.move(fromfile, tofile)

                ProcessGcov(allPaths2gcovs, dirPath)

    if "root" in arguments:
        root = arguments["root"]
    else:
        root = arguments["dirPath"]

    with open(f"{root}/misc/compileErrs.txt", "w") as f:
        f.write(stderrs)

    return

def CollectGcov(allPaths2gcno: list, coveragePath: str):
    """
    """

    total = len(allPaths2gcno)
    count = 1

    allPaths2gcovs = set()

    for path2gcno in allPaths2gcno:
        print (f"{GCOV8} {path2gcno.rstrip()} ({count}/{total})")
        output = subprocess.run([GCOV8, path2gcno], capture_output=True, text=True)
    
        filename = path2gcno.split('.gcno')[0].split('/')[-1]
        path2gcov = filename + ".gcov"
        allPaths2gcovs.add(f"{coveragePath}/{path2gcov}")

        count += 1

    return allPaths2gcovs

def ProcessGcov(allPaths2gcovs: set, coveragePath: str):
    """
    """

    total = len(allPaths2gcovs)
    count = 1

    for path2gcov in allPaths2gcovs:
        print (f"PROCESSING: {path2gcov} ({count}/{total})")

        if os.path.exists(path2gcov):
            statements = General.loadTxtFile(path2gcov)
            stmt2counter = ProcessStmt(statements)

            filename = path2gcov.split('.gcno')[0].split('/')[-1]
            
            if not os.path.exists(f"{coveragePath}/jsons"):
                os.makedirs(f"{coveragePath}/jsons")

            General.dumpToJson(f"{coveragePath}/jsons/{filename}.json", stmt2counter)

        count += 1

    return

def GetFullJson(jsonsPath: str):
    """
    """

    files = os.listdir(jsonsPath)
    fullData = {}
    for f in files:
        if f.endwith(".json"):
            data = General.loadJson(f"{jsonsPath}/{f}")
            fullData |= data
        General.dumpToJson(f"{jsonsPath}/full.json", fullData)

    return

def ProcessStmt(statements: list):
    """
    """

    stmt2counter = {}

    for statement in statements:
        splittedStmt = statement.split(':')
        counter = splittedStmt[0].strip()
        
        if counter.isdigit():
            stmt2counter[statement[12:].strip()] = int(counter)

    return stmt2counter

def CopyGcnoFiles(copy2org_path: dict):
    """
    """

    for copy_path, org_path in copy2org_path.items():
        print (f"COPYING GCNO FILE: {copy_path}")
        print (f"   to {org_path}")
        subprocess.run(["cp", copy_path, org_path])
