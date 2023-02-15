"""
    This file holds the functions that are shared across the files for
    the JS variant generation.

    Author: Anonymous.
"""

import os, sys
import random
import subprocess

from random import seed
from random import randint

# Get current path.
currentdir = os.path.dirname(os.path.realpath(__file__))
# Executable command for nodeJS.
NODEJS = "node"
# Path to JSCodeGenerator.js code.
JSCODEGENERATOR = f"{currentdir}/JSCodeGenerator.js"
# List of operations currently the tool handles.
OPERATIONS = [
              'Literal', 'BinaryExpression', 'UnaryExpression', 'ArrayExpression',
              'ObjectExpression', 'Identifier', 'AssignmentExpression', 'LogicalExpression',
              'ThisExpression'
]
FORLOOP = "ForStatement"
# Seed number to the random number generator.
SEED_INT = 99999

def JSCodeGenerator(rootPath: str, astFilePaths: list):
    """This function generates JavaScript codes based on the AST variants.

    args:
        rootPath (str): root directory where all variants will be stored.
        astFilePaths (list): directory where all AST variants are stored.

    returns:
        None.
    """

    for astFilePath in astFilePaths:
        f = os.path.basename(astFilePath)
        name, ext = os.path.splitext(f)
        JSCodeFilePath = f"{rootPath}/{name}.js"

        subprocess.run([NODEJS, JSCODEGENERATOR, astFilePath, JSCodeFilePath])

def SingleJSCodeGenerator(astpath: str, jspath: str):
    """
    """

    subprocess.run([NODEJS, JSCODEGENERATOR, astpath, jspath])

def ast_editor(ast: dict, target_node_id: int, langInfo: dict, id2edit: dict):
    """This function traverses the original program's ast and edits
    a single  of it.

    args:
      ast (dict): original PoC's syntax tree.
      target_node_id (int):
      langInfo (dict): information about the JS language, such as types and methods, etc.
      id2edit (dict):

    returns:
      None.
    """

    is_loop_edit = [False]
    need_new_target = [False]
    accept = [False]

    while accept[0] == False and need_new_target[0] == False:
        depth = treeModifier(ast, 1, target_node_id, accept, need_new_target, langInfo, is_loop_edit, id2edit)

    return need_new_target[0]

def treeScanner(ast: dict, depth: int):
    """This function recursively traverses the ast and
    returns the number of nodes in the tree. For example,
    each dictionary element is one node in the tree.

    args:
      ast (dict): ast tree.
      depth (int): number of node depther.

    returns:
      (int) number of nodes in the tree.
    """

    if ast:
        for key, value in ast.items():
            if isinstance(value, list):
                for elem in value:
                    depth = treeScanner(elem, depth) + 1
            elif isinstance(value, dict):
                depth = treeScanner(value, depth) + 1

    return depth

def assignIds(ast: dict, depth: int, id2node: dict):
    """This function traverses the syntax tree using the DFS approach,
    and assigns id to each node.

    args:
        ast (dict): ast tree.
        depth (int): depth of tree.
        id2node (dict): node id to node.

    returns:
        (int) current depth of tree.
    """

    if ast:
        for key, value in ast.items():
            if isinstance(value, list):
                for elem in value:
                    depth = assignIds(elem, depth, id2node) + 1
            elif isinstance(value, dict):
                depth = assignIds(value, depth, id2node) + 1

    if not ast or ast["type"] in OPERATIONS:
        id2node[depth] = ast

    return depth

def treeModifier(
        ast: dict, depth: int, target_node_id: int, accept: list,
        need_new_target: list, langInfo: dict, is_loop_edit: list,
        id2edit: dict
):
    """This function recursively scans the tree until endepther
    the node that matches the passed nodeID. It then, calls
    appropriate function to modify the tree and returns.

    args:
      ast (dict): ast tree.
      depth (int): node id tracker.
      target_node_id (int): randomly selected node id.
      accept (list): single element list indicating holding boolean value
      that is False for tree fails to modified or True for tree was modified.
      need_new_target (list): single element list indicating holding boolean value
      that is False for not needing the new target or True for needing a new target.
      langInfo (dict): information about the JS language, such as types and methods, etc.

    returns:
      (dict) modified ast.
    """

    if ast:
        for key, value in ast.items():
            # The line to mark the flag that the loop begin.
            if key == "type" and value == FORLOOP:
                is_loop_edit[0] = True

            if isinstance(value, list):
                for elem in value:
                    depth = treeModifier(
                                elem, depth, target_node_id, accept,
                                need_new_target, langInfo, is_loop_edit,
                                id2edit) + 1
            elif isinstance(value, dict):
                depth = treeModifier(
                            value, depth, target_node_id, accept,
                            need_new_target, langInfo, is_loop_edit,
                            id2edit) + 1
            
            # The line to avoid editing the loop condition.
            if is_loop_edit[0] and key == "test":
                is_loop_edit[0] = False

    # If the current node is not a loop condition node and the node ID is
    # same as the target node id, check additional conditions.
    if not is_loop_edit[0] and depth == target_node_id:
        # If the current node either has no ast property or has ast property
        # and the type is in the OPERATIONS list, which are the language
        # features that we are currently handling.
        if not ast or ast["type"] in OPERATIONS:
            modifyElement(ast, langInfo, id2edit, depth)
            accept[0] = True
        # Otherwise, we need a new target ID to modify the node.
        elif not accept[0]:
            need_new_target[0] = True
    # If the target node is a loop node, then we skip to modify and request for
    # a new target ID to modify.
    elif depth == target_node_id and not accept[0]:
        need_new_target[0] = True

    return depth

def treeModifier2(ast: dict, nodeId: int, nodeIdsToAvoid: list, langInfo: dict, is_loop_edit: list):
    """
    """

    if ast:
        for key, value in ast.items():
            # The line to mark the flag that the loop begin.
            if key == "type" and value == FORLOOP:
                is_loop_edit[0] = True
            else:
                pass

            if isinstance(value, list):
                for elem in value:
                    nodeId = treeModifier2(elem, nodeId, nodeIdsToAvoid, langInfo, is_loop_edit)+1
            elif isinstance(value, dict):
                nodeId = treeModifier2(value, nodeId, nodeIdsToAvoid, langInfo, is_loop_edit)+1
            else:
                pass
            
            # The line to avoid editing the loop condition.
            if is_loop_edit[0] and key == "test":
                is_loop_edit[0] = False

    if not is_loop_edit[0] and nodeId not in nodeIdsToAvoid:
        if not ast or ast["type"] in OPERATIONS:
            modifyElement(ast, langInfo, {}, nodeId)

    return nodeId

def modifyElement(node: dict, langInfo: dict, id2edit: dict, depth: int):
    """This function modifies either binary expression's
    operator or the literal value.

    args:
        node (dict): target node to modify.
        langInfo (dict): information about the JS language, such as types and methods, etc.

    returns:
        None.
    """

    if not node:
        node = literalGenerator("int")
    elif node["type"] == "UnaryExpression":
        changeUnaryExpression(node, langInfo["operators"], id2edit, depth)
    elif node["type"] == "BinaryExpression":
        changeBinaryExpression(node, langInfo["operators"], id2edit, depth)
    elif node["type"] == "ArrayExpression":
        changeArrayExpression(node, langInfo["data-types"], langInfo, id2edit, depth)
    elif node["type"] == "ObjectExpression":
        changeObjectExpression(node, langInfo["data-types"], langInfo["object-types"], langInfo, id2edit, depth)
    elif node["type"] == "Identifier":
        changeIdentifier(node, langInfo["methods"])
    elif node["type"] == "AssignmentExpression":
        changeAssignmentExpression(node, langInfo["operators"]["assignment"])
    elif node["type"] == "LogicalExpression":
        changeLogicalExpression(node, langInfo["operators"]["logical"], id2edit, depth)
    elif node["type"] == "Literal":
        changeLiteral(node)
    elif node["type"] == "ThisExpression":
        changeThisExpression(node)
    #elif node["type"] == "UpdateExpression":
        # TODO: Updating the loop's update can cause an infinite loop. Find the way to
        # solve this problem, then uncomment below.
        # changeUpdateExpression(node, langInfo["operators"]["update"])
    else:
        print(f"WARNING: Skipping element type - {node['type']}.")

## Changers ==========================================================

def changeIdentifier(node: dict, methodInfo: dict):
    """This function checks if the identifier is a JavaScript's built-in
    method and change to other identifier if it is.

    args:
        node (dict): target node to modify.
        methodInfo (dict): information about the JS built-in methods.

    returns:
        None.
    """

    if node["name"] == "undefined":
        # Change node type to "Literal".
        node["type"] = "Literal"
        # Remove (pop) "name" and add "raw" instead with "null".
        node.pop("name", None)
        node["raw"] = "null"
    else:
        sameTypeMethods = []

        # Check if the identifier is a built-in method. If it is, extract
        # the list of same type method names.
        for methodType, methods in methodInfo.items():
            if node['name'] in methods:
                sameTypeMethods = methods

        # If sameTypeMethods is empty, then it's user-written method or variable.
        # Therefore, we don't do anything about it so skip it. Otherwise, we randomly
        # select the same type method and replace it.
        if len(sameTypeMethods) > 0:
            new_identifier = random.choice(sameTypeMethods)
            while new_identifier == node['name']:
                new_identifier = random.choice(sameTypeMethods)
            node['name'] = new_identifier
        else:
            pass

def changeLiteral(node: dict):
    """This function changes the value of literal in the AST.

    args:
        node (dict): target node to modify.
    
    returns:
        None.
    """

    new_value = None

    if "value" not in node and "raw" in node and node["raw"] == "null":
        # Change node type to "Identifier".
        node["type"] = "Identifier"
        # Remove (pop) "raw" and add "name" with "undefined".
        node.pop("raw", None)
        node["name"] = "undefined"
    elif "value" not in node:
        print (f"UNHANDLED NODE: {node}")
    elif isinstance(node["value"], str):
        new_value = "dummy"
        node["raw"] = "\"dummy\""
    elif isinstance(node["value"], bool):
        if node["value"] == True:
            new_value = False
            raw = "false"
        else:
            new_value = True
            raw = "true"
        node["raw"] = raw
    elif isinstance(node["value"], int):
        
        int16_max = 32767
        int32_max = 2147483647
        int64_max = 9223372036854775807

        random_num = 0
        current_value = int(node["value"])
        if current_value < int16_max+1:
            random_num = random.randint(0, int16_max+1)
        elif current_value > int16_max+1 and current_value < int32_max+1:
            random_num = random.randint(0, int32_max+1)
        elif current_value > int32_max+1 and current_value < int64_max+1:
            random_num = random.randint(0, int64_max+1)

        new_value = int(random_num)
        node["raw"] = str(new_value)
    elif isinstance(node["value"], float):
        random_digit = random.random()
        new_value = float(node['value']) + random_digit
        node["raw"] = str(new_value)
    else:
        pass

    if new_value != None:
        # Update literal value with a randomly generated number.
        node["value"] = new_value

def changeBinaryExpression(node: dict, operators: dict, id2edit: dict, depth: int):
    """This function changes the binary expression in the AST.

    args:
        node (dict): target node to modify.
        operators (dict): dictionary of operators.
    
    returns:
        None'.
    """

    current_op = node["operator"]

    if depth not in id2edit:
        id2edit[depth] = [current_op]

    sameTypeOps = []
    for opType, opsList in operators.items():
        if opType != "unary1" and opType != "unary2" and current_op in opsList:
            sameTypeOps = opsList
            break

    if len(sameTypeOps) > 0:
        new_op = random.choice(sameTypeOps)
        while (
                new_op == current_op 
                and new_op in id2edit[depth]
                and len(id2edit[depth]) < len(sameTypeOps)
        ):
            new_op = random.choice(sameTypeOps)

        if new_op not in id2edit[depth]:
            id2edit[depth].append(new_op)
            node["operator"] = new_op

def changeUnaryExpression(node: dict, operators: dict, id2edit: dict, depth: int): 
    """This function changes the unary expression in the AST.

    args:
        node (dict): target node to modify.
    
    returns:
        None.
    """

    current_op = node["operator"]
    unaryList = None

    if depth not in id2edit:
        id2edit[depth] = [current_op]

    if current_op in operators["unary1"]:
        unaryList = operators["unary1"]
    elif current_op in operators["unary2"]:
        unaryList = operators["unary2"]

    if unaryList:
        new_op = random.choice(unaryList)
        while (
                new_op == current_op 
                and new_op in id2edit[depth]
                and len(id2edit[depth]) < len(unaryList)
        ):
            new_op = random.choice(unaryList)

        if new_op not in id2edit[depth]:
            id2edit[depth].append(new_op)
            # Update operation with a randomly selected operator.
            node["operator"] = new_op
    else:
        print (f"WARNING: Unary operator {current_op} not in either 'unary1' or 'unary2' lists.")

def changeArrayExpression(node: dict, dataTypes: list, langInfo: dict, id2edit: dict, depth: int):
    """This function changes the array expression in the AST.

    args:
        node (dict): target node to modify.
        dataTypes (list): list of currently handling JS data types.
    
    returns:
        None.
    """

    if not node["elements"]:
        # randomly decide the number of elements to add.
        dTypeChoice = random.choice(dataTypes)
        # Add only ONE literal type value to the array.
        new_lit = literalGenerator(dTypeChoice)
        node["elements"].append(new_lit)
    else:
        arr_size = len(node["elements"])
        target_idx = randint(0, arr_size-1)
        elem = node["elements"][target_idx]

        modifyElement(elem, langInfo, id2edit, depth)

def changeObjectExpression(
        node: dict, dataTypes: list, objectTypes: list, langInfo: dict, id2edit:dict, depth: int):
    """This function changes the object (map) expression in the AST.

    args:
        node (dict): target node to modify.
        dataTypes (list): list of currently handling JS data types.
        objectTypes (list): list of currently handling JS object types.
    
    returns:
        None.
    """

    if not node["properties"]:
        dType = random.choice(dataTypes + objectTypes)
        # Generate one property and add to the properties list.
        newProperty = propertyGenerator(dType, dataTypes, objectTypes)
        node["properties"].append(newProperty)
    else:
        selected_property = random.choice(node["properties"])
        modifyElement(selected_property["value"], langInfo, id2edit, depth)

def changeUpdateExpression(node: dict, updateOps: list):
    """This function changes the update operators (++/--).

    args:
        node (dict): target node to modify.
        updateOps (list): list of update operators.

    returns:
        None.
    """

    new_op = random.choice(updateOps)
    while new_op == node["operator"]:
        new_op = random.choice(updateOps)
    node["operator"] = new_op

def changeAssignmentExpression(node: dict, assignmentOps: list):
    """This function changes the assignment operators.

    args:
        node (dict): target node to modify.
        assignmentOps: list of assignment operators.

    returns:
        None.
    """

    if node["operator"] in assignmentOps:
        new_op = random.choice(assignmentOps)
        while new_op == node["operator"]:
            new_op = random.choice(assignmentOps)
        node["operator"] = new_op
    elif node["operator"] != "=":
        print(f"WARNING: Assignment operator {node['operator']} is not in the 'assignment' list.")

def changeLogicalExpression(node: dict, logicalOps: list, id2edit: dict, depth: int):
    """this function changes the logical operators.

    args:
        node (dict): target node to modify.
        logicalOps (list): list of logical operators.

    returns:
        None.
    """

    current_op = node["operator"]

    if depth not in id2edit:
        id2edit[depth] = [current_op]
       
    if current_op in logicalOps:
        new_op = random.choice(logicalOps)
        while (
                new_op == current_op 
                and new_op in id2edit[depth]
                and len(id2edit[depth]) < len(logicalOps)
        ):
            new_op = random.choice(logicalOps)

        if new_op not in id2edit[depth]:
            id2edit[depth].append(new_op)
            node["operator"] = new_op
    else:
        print(f"WARNING: Logical operator {node['operator']} is not in the 'logical' list.")

def changeThisExpression(node: dict):
    """This function changes the this expression.

    args:
        node (dict): target node to modify.

    returns:
        None.
    """

    change_to = ["undefined", "null"]

    selected = random.choice(change_to)

    if selected == "undefined":
        node["type"] = "Identifier"
        node["name"] = "undefined"
    else:
        node["type"] = "Literal"
        node["raw"] = "null"

## Generators ========================================================

def literalGenerator(dType: str):
    """This function generates a syntax structure for Literal
    type with some random literal values.

    args:
      dType (str): Data type to generate.

    returns:
      (dict) new literal structure dict.
    """
    # Prepare new structure.
    new_struct = {'type': "Literal"}

    rand_value = None

    if dType == "int":
        # Generate random number.
        rand_value = randint(0, 99999)
        new_struct['raw'] = str(rand_value)
    elif dType == "str":
        rand_value = "dummy"
        new_struct['raw'] = "\"dummy\""
    elif dType == "bool":
        rand_value = random.choice([True, False])
        new_struct['raw'] = str(rand_value)

    if rand_value != None:
        # Populate new_struct with value and raw.
        new_struct['value'] = rand_value

    return new_struct

def propertyGenerator(dType: str, dataTypes: list, objectTypes: list):
    """This function generates property (element) of a map.

    args:
      dType (str): Data type to generate.
      dataTypes (list): list of currently handling JS data types.
      objectTypes (list): list of currently handling JS object types.

    returns:
      (dict) new map property dict.
    """

    # Prepare a default structure of a property.
    property = {
                  "type": "Property",
                  "key": {
                            "type": "Identifier",
                            "name": "dummy"
                  },
                  "value": {},
                  "computed": False,
                  "kind": "init",
                  "method": False,
                  "shorthand": False
    }

    if dType in dataTypes:
        property["value"] = literalGenerator(dType)
    elif dType == objectTypes[0]: # dType is array.
        property["value"] = arrayGenerator()
    elif dType == objectTypes[1]: # dType is map.
        property["value"] = mapGenerator()
    else:
        assert (
            False
        ), f"ERROR: Type {dType} is not a valid type."

    return property

def arrayGenerator():
    """This function generates array structure.
    For now, it's only generating an empty array.

    args:
      None.

    returns:
      None.
    """
    
    # Prepare a default structure of an array.
    array = {"type": "ArrayExpression", "elements": []}

    return array

def mapGenerator():
    """This function generates map structure.
    For now, it's only generating an empty map.

    args:
      None.

    returns:
      None.
    """

    # Prepare a default structure of a map.
    map = {"type": "ObjectExpression", "properties": []}

    return map
