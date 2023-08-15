import os, sys
import random
import copy
import json

def selectTarget(total_nodes: int, skip_ids: set):
    """This function selected target AST node ID to mutate.

    args:
        total_nodes (int): total number of nodes.
        skip_ids (set): set of node ids to skip.

    returns:
        (int) target node id.
    """
    
    target = random.randint(3, total_nodes)
    while target in skip_ids:
        target = random.randint(1, total_nodes)

    return target

def treeScanner(
        ast: dict, depth: int, skip_ids: set, function_names: set,
        nodetypes: dict, labels: set):
    """This function traverse AST tree for the two tasks:
        (1) count the number of nodes.
        (2) identify the nodes to skip for mutation.

    args:
        ast (dict): ast to scan.
        depth (int): tree depth.
        skip_ids (set): set to hold node ids to skip.
        function_names (set): set to hold function names.
        labels (set): lable IDs from Label nodes.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        skip_ids = check_skips(
                                ast, key, depth, skip_ids, 
                                function_names, nodetypes,
                                labels)
                        for elem in value:
                            if elem != dict:
                                skip_ids.add(depth)
                            depth = treeScanner(
                                    elem, depth, skip_ids, 
                                    function_names, nodetypes,
                                    labels) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    skip_ids = check_skips(
                            ast, key, depth, skip_ids, 
                            function_names, nodetypes,
                            labels)
                    depth = treeScanner(
                            value, depth, skip_ids, 
                            function_names, nodetypes,
                            labels) + 1
                else:
                    depth += 1
        else:
            depth += 1
    
    skip_ids = check_skips(
            ast, "", depth, skip_ids, function_names,
            nodetypes, labels)

    return depth

def astEditor(
        ast: dict, target_node_id: int, lang_info: dict,
        depth: int, skip_ids: set, function_names: set,
        nodetypes: dict, labels: set, edited_nodeId: list):
    """This function traverses the ast and seek for the target node 
    by comparing the passed target node id. Then, if found, edits 
    (mutates) the node.

    args:
        ast (dict): ast to scan.
        target_node_id (int): target node id to edit.
        lang_info (dict): language information.
        depth (int): tree depth.
        skip_ids (set): set of node ids to skip.
        function_names (set): set of function names in the code.
        labels (set): lable IDs from Label nodes.
        edited_nodeId (list): a single element list that holds
        the id of edited node.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        for elem in value:
                            depth = astEditor(
                                    elem, target_node_id, 
                                    lang_info, depth, skip_ids, 
                                    function_names, nodetypes,
                                    labels, edited_nodeId) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    if depth == target_node_id:
                        is_edited = edit_node(
                                ast, ast[key], lang_info, 
                                function_names, nodetypes, 
                                labels)
                        if is_edited:
                            edited_nodeId[0] = depth
                        return depth
                    depth = astEditor(
                            value, target_node_id, 
                            lang_info, depth, skip_ids, 
                            function_names, nodetypes,
                            labels, edited_nodeId) + 1
                else:
                    depth += 1
        else:
            depth += 1

    if '_nodetype' in ast and depth == target_node_id:
        is_edited = edit_node(
                ast, ast, lang_info, function_names, 
                nodetypes, labels)
        edited_nodeId[0] = depth

    return depth

def edit_node(
        parent: dict, current: dict, lang_info: dict, function_names: set,
        nodetypes: dict, labels: set):
    """This function edits the node if the node is a non-block node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language info.
        function_names (set): set of function names.
        labels (set): lable IDs from Label nodes.

    returns:
        None.
    """

    is_edited = True

    assert (
        '_nodetype' in current
    ), f"ERROR: '_nodetype' does not exist in the AST node: {node[key]}"

    _nodetype = current['_nodetype']

    if '_nodetype' in parent and parent['_nodetype'] in nodetypes['skips']:
        is_edited = False
    elif _nodetype == 'Constant':
        constantType = current['type']
        current = modify_number(parent, current)
    elif _nodetype == 'UnaryOp':
        current = modify_unary(parent, current, lang_info)
    elif _nodetype == 'BinaryOp':
        current = modify_binary(parent, current, lang_info)
    elif _nodetype == 'TypeDecl':
        current = modify_typeDecl(parent, current, lang_info, function_names)
    elif _nodetype == 'Assignment':
        current = modify_assignment(parent, current, lang_info)
    elif _nodetype == 'Typename':
        current = modify_typename(parent, current, lang_info)
    elif _nodetype == 'Decl':
        current = modify_decl(parent, current, lang_info, function_names)
    elif _nodetype == 'Goto':
        current = modify_goto(parent, current, lang_info, labels)
    elif _nodetype == 'Continue' or _nodetype == 'Break':
        current = modify_loop_cf(current)
    elif _nodetype in nodetypes['skips']:
        is_edited = False
    else:
        is_edited = False
        print (f"WARNING: _nodetype {_nodetype} is not handle yet...")
        print (f"|__current: {current}")
        print (f"   |__parent: {parent}")

    return is_edited

def modify_number(parent: dict, current: dict):
    """This function modifies the constant value node if the value is
    a number type.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.

    returns:
        (dict) modified node.
    """

    if '_nodetype' in parent and parent['_nodetype'] == 'Decl':
        valType = ' '.join(parent['type']['type']['names'])
    else:
        valType = current['type']

    value = 0
    if valType == 'char' or valType == 'unsigned char':
        if random.randint(0, 9) % 2 == 0:
            value = random.randint(65, 90)
        else:
            value = random.randint(97, 122)
        value = f"'{chr(value)}'"
    elif valType == 'signed char':
        value = random.randint(0, 127)
    elif valType == 'int':
        value = random.randint(0, 2147483647)
    elif valType == 'unsigned int':
        value = random.randint(0, 4294967295)
    elif valType == 'short' or valType == 'short int':
        value = random.randint(0, 32767)
    elif valType == 'unsigned short' or valType == 'unsigned short int':
        value = random.randint(0, 65535)
    elif valType == 'long' or valType == 'long int':
        value = random.randint(0, 9223372036854775807)
    elif valType == 'unsigned long' or valType == 'unsigned long int':
        value = random.randint(0, 18446744073709551615)
    elif valType == 'float':
        value = random.uniform(0, 3.4e38)
    elif valType == 'double':
        value = random.uniform(0, 1.7e308)
    elif valType == 'long dobule':
        value = random.randint(0, 1.1e4932)
    else:
        print(f"WARNING: Value type {valType} not handled...")

    current['value'] = str(value)

    return current

def modify_unary(parent: dict, current: dict, lang_info: dict):
    """This function modifies unary node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.

    returns:
        (dict) modified node.
    """

    operators = lang_info['operators']

    node_op = current['op']

    if node_op == "!":
        print ("WARNING: Unary op is '!'...")
        return current
    
    op = ""
    for k, values in operators.items():
        if node_op in values:
            op = random.choice(values)
            while op == node_op:
                op = random.choice(values)
            break
    
    if not op:
        print ("WARNING: Unary op is empty...")
    else:
        current['op'] = op

    return current

def modify_binary(parent: dict, current: dict, lang_info: dict):
    """This function modifies binary node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.

    returns:
        (dict) modified node.
    """

    operators = lang_info['operators']

    node_op = current['op']

    for key, value in operators.items():
        if node_op in value:
            op = random.choice(value)
            while op == node_op:
                op = random.choice(value)
            break
    
    current['op'] = op

    return current

def modify_typeDecl(parent: dict, current: dict, lang_info: dict, function_names: set):
    """This function modifies typeDecl node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.
        function_names (set): set of function names.

    returns:
        (dict) modified node.
    """

    declname = current['declname']
    
    if declname in function_names:
        return current
    elif current['type']['_nodetype'] == 'Struct':
        return current
    else:
        typename = ' '.join(current['type']['names'])
        dataTypes = lang_info['data-types']
        nodeTypeNames = current['type']['names']
        # Default set the target name element to its first element.
        targetNameIdx = 0
        # Default choice of the new type is selected randomly.
        new_type = random.choice(nodeTypeNames)

        if len(nodeTypeNames) == 1:
            name = nodeTypeNames[0]

            for k, dTypes in dataTypes.items():
                if name in dTypes and len(dTypes) > 1:
                    new_type = random.choice(dTypes)
                    while new_type == name:
                        new_type = random.choice(dTypes)
                    break
        else:
            targetNameIdx = random.randint(0, len(nodeTypeNames)-1)
            name = nodeTypeNames[targetNameIdx]

            for k, dTypes in dataTypes.items():
                if name in dTypes and len(dTypes) > 1:
                    new_type = random.choice(dTypes)
                    while new_type == name:
                        new_type = random.choice(dTypes)
                    break

        assert (
            new_type != None
        ), f"ERROR: New type is empty."

        current['type']['names'][targetNameIdx] = copy.deepcopy(new_type)

    return current

def modify_assignment(parent: dict, current: dict, lang_info: dict):
    """This function modifies Assignment node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.

    returns:
        (dict) modified node.
    """

    assert (
        current['_nodetype'] == 'Assignment'
    ), f"ERROR: _nodetype in modify_assignment is not 'Assignment': {current}."

    op = current['op']

    if op == '=':
        return current
    else:
        operators = lang_info['operators']

        for key, value in operators.items():
            if op in value:
                new_op = random.choice(value)
                while new_op == op:
                    new_op = random.choice(value)
                current['op'] = copy.deepcopy(new_op)
                break

    return current

def modify_typename(parent: dict, current: dict, lang_info: dict):
    """This function modifies Typename node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.

    returns:
        (dict) modified node.
    """

    assert (
        current['_nodetype'] == 'Typename'
    ), f"ERROR: _nodetype in modify_typename is not 'Typename': {current}."

    if not current['quals']:
        return current
    else:
        qualifiers = lang_info['qualifiers1']

        quals = current['quals']
        
        new_quals = []
        for qual in quals:
            new_qual = random.choice(qualifiers)
            while new_qual == qual:
                new_qual = random.choice(qualifiers)
            new_quals.append(new_qual)

        current['quals'] = copy.deepcopy(new_quals)
        current['type']['type']['quals'] = copy.deepcopy(new_quals)

    return current

def modify_decl(parent: dict, current: dict, lang_info: dict, function_names: set):
    """This function modifies the decl node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.
        function_names (set): set of function names.

    returns:
        (dict) modified node.
    """

    assert (
        current['_nodetype'] == 'Decl'
    ), f"ERROR: _nodetype in modify_decl is not 'Decl': {current}."

    name = current['name']

    if name in function_names:
        return current
    elif not current['quals']:
        return current
    else:
        assert (
            len(current['quals']) > 0
        ), f"ERROR: current['quals'] is empty."

        qualifiers = lang_info['qualifiers1']

        quals = current['quals']
        
        new_quals = []
        for qual in quals:
            new_qual = random.choice(qualifiers)
            while new_qual == qual:
                new_qual = random.choice(qualifiers)
            new_quals.append(new_qual)

        current['quals'] = copy.deepcopy(new_quals)
        current['type']['quals'] = copy.deepcopy(new_quals)

    return current

def modify_goto(parent: dict, current: dict, lang_info: dict, labels: set):
    """This function modifies Goto node.

    args:
        parent (dict): parent node of the current.
        current (dict): current node to edit.
        lang_info (dict): language information.
        labels (set): lable IDs from Label nodes.

    returns:
        (dict) modified node.
    """

    assert (
        current['_nodetype'] == 'Goto'
    ), f"ERROR: _nodetype in modify_goto is not 'Goto': {current}."

    if len(labels) == 1:
        return current
    else:
        name = current['name']
        new_name = random.choice(list(labels))
        while new_name == name:
            new_name = random.choice(list(labels))
        current['name'] = new_name

    return current

def modify_loop_cf(current: dict):
    """This function modifies either Continue or Break node.

    args:
        current (dict): current node to edit.

    returns:
        (dict) modified node.
    """

    _nodetype = current['_nodetype']

    assert (
        _nodetype == 'Continue' or
        _nodetype == 'Break'
    ), f"ERROR: _nodetype in modify_loop_cf is neither Continue nor Break: {current}."

    if _nodetype == 'Break':
        current['_nodetype'] = 'Continue'
    else:
        current['_nodetype'] = 'Break'

    return current

def check_skips(
        node: dict, key: str, depth: int, skip_ids: set, 
        function_names: set, nodetypes: dict, labels: set):
    """This function checks if we want to skip the node during 
    the mutation. If yes, it adds the node ID in the skip_ids set.

    This function is needed because the nodes with identified node types 
    for skipping are too coarse or changing it won't make any changes to 
    the source code. Thus, identify the node's IDs (AST depth) during the 
    initial tree scanning, and skip them while editing can increase the 
    efficiency of the tool.

    args:
        node (dict): node dictionary.
        key (str): key of the node.
        depth (int): depth of the tree, i.e., a node id.
        skip_ids (set) set of node ids to skip.
        function_names (set): set to hold function names.
        labels (set): lable IDs from Label nodes.

    return:
        (set) set of node ids.
    """

    if key == 'ext' or key == 'body':
        skip_ids.add(depth)
    elif '_nodetype' in node and node['_nodetype'] in nodetypes['skips']:
        if node['_nodetype'] == 'FuncDecl':
            # We do not want to skip function declaration node, 
            # but we don't want to modify it yet. Thus, we only 
            # keep a track of function names for now.
            function_names.add(node['type']['declname'])
        elif node['_nodetype'] == 'IdentifierType':
            # We update 'IdentifierType' node through its parent,
            # i.e., typeDecl, because typeDecl node holds the
            # identifier's name. 'IdentifierType' only holds the
            # identifier's type.
            pass
        elif node['_nodetype'] == 'Label':
            # We want to keep a track of all label names (IDs).
            labels.add(node['name'])
        else:
            skip_ids.add(depth)

    return skip_ids

def load_json(json_file: str):
    """This function loads JSON and returns if the file is valid.
    Otherwise, it throws an error and terminates the program.

    args:
        json_file (str): path to json file.

    returns:
        (dict) loaded IR.
    """
        
    try:
        with open(json_file) as f:
            return json.load(f)
    except IOError as x:
        assert False, f"{json_file} cannot be opened."
