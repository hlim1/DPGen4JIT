import os, sys
import random

SKIP_NODETYPES = ['FuncDef', 'FileAST']

C_DATATYPES = [
        'char', 
        'unsigned char', 
        'signed char',
        'int', 
        'unsigned int',
        'shart',
        'unsigned short',
        'long',
        'unsigned long',
        'float',
        'double',
        'long double'

]

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

def treeScanner(ast: dict, depth: int, skip_ids: set):
    """This function traverse AST tree for the two tasks:
        (1) count the number of nodes.
        (2) identify the nodes to skip for mutation.

    args:
        ast (dict): ast to scan.
        depth (int): tree depth.
        skip_ids (set): set of node ids to skip.

    returns:
        (int) tree depth.
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        if key == 'ext' or key == 'body':
                            skip_ids.add(depth)
                        elif '_nodetype' in ast and ast['_nodetype'] in SKIP_NODETYPES:
                            skip_ids.add(depth)
                        for elem in value:
                            if elem != dict:
                                skip_ids.add(depth)
                            depth = treeScanner(elem, depth, skip_ids) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    if key == 'ext' or key == 'body':
                        skip_ids.add(depth)
                    elif '_nodetype' in ast and ast['_nodetype'] in SKIP_NODETYPES:
                        skip_ids.add(depth)
                    depth = treeScanner(value, depth, skip_ids) + 1
                else:
                    depth += 1
        else:
            depth += 1
    
    if '_nodetype' in ast and ast['_nodetype'] in SKIP_NODETYPES:
        skip_ids.add(depth)

    return depth

def ast_editor(
        ast: dict, target_node_id: int, lang_info: dict,
        id2edit: dict, depth: int, skip_ids: set):
    """
    """

    if ast:
        if type(ast) == dict:
            for key, value in ast.items():
                if isinstance(value, list):
                    if value:
                        for elem in value:
                            if depth == target_node_id:
                                edit_block(elem)
                            depth = ast_editor(elem, target_node_id, 
                                    lang_info, id2edit, depth, skip_ids) + 1
                    else:
                        depth += 1
                elif isinstance(value, dict):
                    if depth == target_node_id:
                        edit_dict(ast, key, lang_info)
                    depth = ast_editor(value, target_node_id, 
                            lang_info, id2edit, depth, skip_ids) + 1
                else:
                    depth += 1
        else:
            depth += 1

    return depth

def edit_dict(node: dict, key: str, lang_info: dict):
    """
    """

    assert (
        '_nodetype' in node[key]
    ), f"ERROR: '_nodetype' does not exist in the AST node: {node[key]}"

    _nodetype = node[key]['_nodetype']

    if _nodetype == 'Constant':
        constantType = node[key]['type']
        node = modify_number(node, key)
    elif _nodetype == 'IdentifierType':
        names = node[key]['names']
        if len(names) > 1:
            pass
        else:
            pass
    elif _nodetype == 'UnaryOp':
        node = modify_unary(node, key, lang_info)
    else:
        print (f"WARNING: _nodetype {_nodetype} is not being handle yet...")
        print (f"|__{node[key]}")

def edit_block(node: dict):
    """
    """

    assert (
        '_nodetype' in node
    ), f"ERROR: '_nodetype' does not exist in the AST node: {node}"

    _nodetype = node['_nodetype']

def modify_number(node: dict, key: str):
    """This function modifies the constant value node if the value is
    a number type.

    args:
        node (dict): node dictionary.
        key (str): key of the node.

    returns:
        (dict) modified node.
    """

    if '_nodetype' in node and node['_nodetype'] == 'Decl':
        valType = ' '.join(node['type']['type']['names'])
    else:
        valType = node[key]['type']

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

    node[key]['value'] = str(value)

    return node

def modify_unary(node: dict, key: str, lang_info: dict):
    """This function modified the unary operator.

    args:
        node (dict): node dictionary.
        key (str): key of the node.
        lang_info (dict): language information.

    returns:
        (dict) modified node.
    """

    operators = lang_info['operators']

    node_op = node[key]['op']

    if node_op == "!":
        print ("WARNING: Unary op is '!'...")
        return node
    
    op = ""
    for k, values in operators.items():
        if node_op in values:
            op = random.choice(values)
            break
    
    if not op:
        print ("WARNING: Unary op is empty...")
    else:
        node[key]['op'] = op

    return node
