/*
 *  This program convers AST tree into JS Code, if valid.
 *  It uses escodegen (https://github.com/estools/escodegen).
 *
 *  Author: Anonymous.
 */


const fs = require('fs')
const escodegen = require('escodegen');

var cmd_argument = process.argv

if (cmd_argument.length > 4) {
    throw "ERROR: Too many command-line arguments."
}

var input_file  = cmd_argument[2]
var output_file = cmd_argument[3]

fs.readFile(input_file, (err, data) => { 
    if (err) throw err; 
   
    var string_ast = data.toString();
    // Convert read in syntax tree in a string type to JSON for parsing. 
    ast = JSON.parse(string_ast);
    // Generate JS code from AST.
    var code = escodegen.generate(ast);

    fs.writeFile(output_file, code, function(err) {
        if (err) {
            return console.error(err);
        }
    });
})
