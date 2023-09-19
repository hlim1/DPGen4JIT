import os, sys
import copy
import subprocess

def RunOracle(arguments: dict, binsPath: str, CFiles: set, _iptDir: str):
    """
    """

    # Number of compilers the user specified to use as Oracle.
    numberOfComps = arguments["numberOfComps"]

    binPaths = GetBinPaths(binsPath)

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

    stderrs = ""
    
    originalCMD = copy.deepcopy(commands)
    for c_file in CFiles:
        binPath, output = GenerateBin(c_file, binsPath, commands, compiler)
        commands = copy.deepcopy(originalCMD)

        if output.stderr:
            stderrs += f"{output.stderr}\n"
            if not "error" in output.stderr:
                binPaths.add(binPath)
        else:
            binPaths.add(binPath)

    if "root" in arguments:
        root = arguments["root"]
    else:
        root = arguments["dirPath"]

    with open(f"{root}/misc/compileErrs.txt", "w") as f:
        f.write(stderrs)

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

    return binPath, output

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
                # ONLY FOR BUG #16605
                # output = subprocess.run([f"{binPath}", ";", "echo", "$?"], capture_output=True, text=True, timeout=10)
            except subprocess.TimeoutExpired:
                print (f"   TIMEOUT: {compiler}: {binPath}...")
                fileIdsToExc.add(fileId)
                continue
            fileId2output[fileId] = f"{output.returncode},{output.stdout},{output.stderr}"

    return fileId2output, fileIdsToExc

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

    outputs = {}

    # First run all binary executables generated from the target (buggy) compiler.
    target_fileId2output, fileIdsToExc = RunBins(target, binPaths)
    # Initialize the voting count for each output of each execution with 1.
    for fileId, output in target_fileId2output.items():
        outputs[fileId] = [output]

    for compiler, paths in compiler2BinPaths.items():
        fileId2output, fileIdsToExc = RunBins(compiler, paths)
        for fileId, output in fileId2output.items():
            if fileId in outputs and fileId not in fileIdsToExc:
                if output not in outputs[fileId]:
                    outputs[fileId].append(output)
            elif fileId in fileIdsToExc:
                del outputs[fileId]

    buggyIds = set()
    nonbuggyIds = set()
    for fileId, output_info in outputs.items():
        print (f"FILEID2OUTPUT: {fileId}: {output_info}")
        if len(output_info) == 1:
            nonbuggyIds.add(int(fileId))
        elif len(output_info) == 2:
            buggyIds.add(int(fileId))
        else:
            continue


    # General.dumpToJson("./voting.json", voting)
    return buggyIds, nonbuggyIds

def GetBinPaths(binsPath: str):
    """
    """

    paths = set()

    bins = os.listdir(binsPath)
    
    for binfile in bins:
        paths.add(f"{binsPath}/{binfile}")

    return paths


