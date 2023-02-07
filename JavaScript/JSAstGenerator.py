"""
    This program is for converting input JavaScript code to AST Tree.
    The function used esprima-python (https://github.com/Kronuz/esprima-python).
    Due to the limitation of esprima-python that it can handle ECMAScript 2017 standard,
    the JS Language features above cannot be handled.

    Autho: Anonymous.
"""

import esprima
import argparse

def AstGenerator(JSCode: str):
    """This function receives the target JS code and
    generates abstract syntax tree using esprima. Then,
    returns the generated ast.

    args:
        JSCode (str): JS code that is target for ast
        generation.

    returns:
        (dict) generated absract syntax tree.
    """

    ast = esprima.parseScript(JSCode)

    assert ast, f"ERROR: ast is empty."

    return ast 

def argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-f",
            "--file",
            type=str,
            required=True,
            help="JavaScript file to generate variants from."
    )
    args = parser.parse_args()

    return args.file

if __name__ == "__main__":
    jsFilePath = argument_parser()

    with open(jsFilePath) as jsFile:
        jsCode = jsFile.read()

        ast = AstGenerator(jsCode)

        print (ast.toDict())
