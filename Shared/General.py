import json

def dumpToJson(filepath: str, target: dict):

    try:
        converted = json.dumps(target, indent=4)
        with open(filepath, "w") as f:
            f.write(converted)
    except IOError as x:
        assert False, f"{filePath} cannot be opened."

def loadJson(json_file: str):
        
    try:
        with open(json_file) as f:
            return json.load(f)
    except IOError as x:
        assert False, f"{json_file} cannot be opened."


