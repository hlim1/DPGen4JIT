import os, sys
import subprocess
import copy

# Code to import modules from other directories.
# Soruce: https://codeolives.com/2020/01/10/python-reference-module-in-parent-directory/
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)

import DPGen4JIT.Shared.General as General

def GenerateBins(CFiles: set, binsPath: str, arguments: dict, commands: list, compiler: str):
    """This function generates binary executables from 
    the generated C files.

    args:
        CFiles (set): set of C file paths.
        binsPath (str): path to directory where gengerated
        binary files will be stored.
        arguments (dict): arguments to the system.
        commands (list): command-line arguments to compiler the C file.
        compiler (str): name of the compiler used in compiling the C file.

    returns:
        (set) set of generated binary file paths.
    """

    binPaths = set()
    
    originalCMD = copy.deepcopy(commands)
    for c_file in CFiles:
        binPath = GenerateBin(c_file, binsPath, commands, compiler)
        commands = copy.deepcopy(originalCMD)

        binPaths.add(binPath)

    return binPaths

def GenerateBin(CFile: str, binsPath: str, commands: list, compiler: str):
    """This function generates a single binary executable for the given
    C program file.

    args:
        CFile (str): path to C program file to compile.
        binsPath (str): path to directory where gengerated
        binary files will be stored.
        commands (list): command-line arguments to compiler the C file.
        compiler (str): name of the compiler used in compiling the C file.

    returns:
        (str) path of a binary executable file.
    """
    
    fileId = (CFile.split('__')[-1]).split('.')[0]
   
    binPath = f"{binsPath}/{compiler}_bin__{fileId}"

    commands.append(CFile)
    commands.append("-o")
    commands.append(binPath)

    output = subprocess.run(commands, capture_output=True, text=True)
    
    return binPath

def RunBins(compiler: str, binPaths: set):
    """This function runs all binaries, and collect the output (result) of running
    the binary.

    args:
        compiler (str): name of the compiler used in compiling the C file.
        binPaths (set): set of binary executable paths.

    returns:
        (dict): file id to output.
    """

    fileId2output = {}
    fileIdsToExc = set()

    total = len(binPaths)
    count = 1

    for binPath in binPaths:
        if os.path.exists(binPath):
            progress = round((count/total)*100)
            print (f"RUNNING BIN: {compiler}: {binPath} ({progress}%)...")
            count += 1

            fileId = (binPath.split('__')[-1]).split('.')[0]
            try:
                output = subprocess.run([binPath], capture_output=True, text=True, timeout=10)
            except subprocess.TimeoutExpired:
                print (f"   TIMEOUT: {compiler}: {binPath}...")
                fileIdsToExc.add(fileId)
                continue
            fileId2output[fileId] = f"{output.returncode},{output.stdout},{output.stderr}"

    return fileId2output, fileIdsToExc

def IdentifyTargetNodeIDs(nonbuggyIds: set, fileId2NodeId: dict):
    """This function identifies the target node IDs to edit during
    the directed mutation process.

    args:
        nonbuggyIds (set): set of non-buggy file IDs.
        fileId2NodeId (dict): file id to edited node ID.

    returns:
        (set) set of target node IDs.
    """

    nodeIds = set()

    for fileId in nonbuggyIds:
        if fileId in fileId2NodeId:
            nodeIds.add(fileId2NodeId[fileId])

    return nodeIds

def Oracle(target: str, binPaths: set, compiler2BinPaths: dict):
    """This function checks if the test program is a pass or fail.

    args:
        binPaths (set): set of paths for all binary executable files
        generated using the target (buggy) compiler.
        compiler2BinPaths (dict): compiler name to binary executable
        paths.

    returns:
        (set) set of buggy file IDs.
        (set) set of non-buggy file IDs.
    """

    voting = {}

    # First run all binary executables generated from the target (buggy) compiler.
    target_fileId2output, fileIdsToExc = RunBins(target, binPaths)
    # Initialize the voting count for each output of each execution with 1.
    for fileId, output in target_fileId2output.items():
        voting[fileId] = {output:1}

    for compiler, paths in compiler2BinPaths.items():
        fileId2output, fileIdsToExc = RunBins(compiler, paths)
        for fileId, output in fileId2output.items():
            if fileId in voting and fileId not in fileIdsToExc:
                if output in voting[fileId]:
                    voting[fileId][output] += 1
                else:
                    voting[fileId][output] = 1
            elif fileId in fileIdsToExc:
                del voting[fileId]

    buggyIds = set()
    nonbuggyIds = set()
    for fileId, output_info in voting.items():
        if len(output_info) == 1:
            nonbuggyIds.add(int(fileId))
        elif len(output_info) == 2:
            for output, count in output_info.items():
                if (
                    output == target_fileId2output[fileId] and
                    count == 1
                ):
                    buggyIds.add(int(fileId))
        else:
            pass

    # General.dumpToJson("./voting.json", voting)
    return buggyIds, nonbuggyIds

def RunOracle(arguments: dict, binsPath: str, CFiles: set, _iptDir: str):
    """

    args:
        arguments (dict): arguments to the system.
        binsPath (str): path to directory where gengerated
        binary files will be stored.
        CFiles (set): set of C file paths.
        _iptDir (str): path to the directory where generated
        input C programs are stored.

    returns:
        (set) set of buggy file IDs.
        (set) set of non-buggy file IDs.
    """

    # Number of compilers the user specified to use as Oracle.
    numberOfComps = arguments["numberOfComps"]

    # First generate the binaries using the target (buggy) compiler.
    commands = [arguments["compilerPath"]]
    commands.extend(arguments["arguments"])
    print (f"BIN. GENERATION: {arguments['compilerPath']}...")
    binPaths = GenerateBins(
            CFiles, binsPath, arguments, commands, arguments["compiler"])

    # For each user-specified compilers to be used in Oracle, generate binary 
    # files for all the generated C test programs.
    compiler2BinPaths = {}
    for i in range(1, numberOfComps+1):
        compilerKey = f"compiler{i}"
        assert (
            compilerKey in arguments
        ), f"ERROR: Key ({compilerKey}) to get compiler command-line argument does not exist."
        compCLA = copy.deepcopy(arguments[compilerKey])
        # Generate a directory under _iptDir to hold binaries generated with
        # the compiler used in Oracle. The name of the directory is the same as the
        # compiler's executable bin (e.g., gcc, g++, icc, etc.)
        compBinsPath = f"{_iptDir}/{compCLA[0]}"
        if not os.path.exists(compBinsPath):
            os.makedirs(compBinsPath)
        print (f"BIN. GENERATION: {compCLA[0]}...")
        bins4OraclePaths = GenerateBins(CFiles, compBinsPath, arguments, compCLA, compCLA[0])
        compiler2BinPaths[compCLA[0]] = copy.deepcopy(bins4OraclePaths)
    
    # Classify C files into two groups: buggy and non-buggy.
    buggyIds, nonbuggyIds = Oracle(arguments["compiler"], binPaths, compiler2BinPaths)

    return buggyIds, nonbuggyIds

def CLearning(
        arguments: dict, binsPath: str, CFiles: set, random_iptDir: str,
        fileId2NodeId: dict):
    """This function analyze the generated C test programs by running
    the binaries. The analysis is to identify the following:
    (1) test programs to classify the test programs into two groups,
    i.e., passing or failing.
    (2) identify the AST nodes of the original seed program that eliminated
    the buggy behavior via modificaiton.

    args:
        arguments (dict): arguments to the system.
        binsPath (str): path to directory where gengerated
        binary files will be stored.
        CFiles (set): set of C file paths.
        random_iptDir (str): path to the directory where randomly generated
        input C programs are stored.
        fileId2NodeId (dict): file id to edited node ID.

    returns:
        (set) set of target node IDs.
    """

    buggyIds, nonbuggyIds = RunOracle(arguments, binsPath, CFiles, random_iptDir)
    print (f"UNDIRECTED: Buggy IDs: {buggyIds}")
    print (f"UNDIRECTED: NonBuggy IDs: {nonbuggyIds}")

    # Identify target node IDs to edit during the directed mutation.
    nodeIds = IdentifyTargetNodeIDs(nonbuggyIds, fileId2NodeId)

    return nodeIds

if __name__ == "__main__":

    #executable_path = "/scratch/hlim1/Pin/DPGen4JIT/Tests/C/bug16041/fail"
    executable_path = "/scratch/hlim1/Pin/DPGen4JIT/Tests/C/bug16041/pass"
    Oracle(executable_path)
