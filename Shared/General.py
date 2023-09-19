import json

def dumpToJson(filepath: str, target: dict):

    try:
        converted = json.dumps(target, indent=4)
        with open(filepath, "w") as f:
            f.write(converted)
    except IOError as x:
        assert False, f"{filepath} cannot be opened."

def loadJson(json_file: str):
        
    try:
        with open(json_file) as f:
            return json.load(f)
    except IOError as x:
        assert False, f"{json_file} cannot be opened."

def loadTxtFile(filepath: str):

    with open(filepath) as f:
        lines = f.readlines()

    return lines

def SortDictByKey(dictTosort: dict):

    keysOnly = list(dictTosort.keys())
    keysOnly.sort()
    sorted_dict = {i:dictTosort[i] for i in keysOnly}

    return sorted_dict

def SortDictByValues(dictToSort: dict, reverse=True):

    sorted_dict = sorted(
            dictToSort.items(), key=lambda x:x[1], reverse=reverse)

    return dict(sorted_dict)
