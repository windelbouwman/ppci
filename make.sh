#!/bin/bash

python bin/yacc.py ppci/target/arm/assembler.grammar -o ppci/target/arm/parser.py
python bin/yacc.py ppci/burg.grammar -o ppci/burg_parser.py

