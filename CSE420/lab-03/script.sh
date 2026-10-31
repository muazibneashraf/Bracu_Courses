#!/bin/bash

set -e

SOURCE_Y="21101177.y"
SOURCE_L="21101177.l"
INPUT_FILE="${1:-input.c}"

if command -v bison >/dev/null 2>&1; then
    bison -d -y "$SOURCE_Y"
elif command -v yacc >/dev/null 2>&1; then
    yacc -d -y "$SOURCE_Y"
else
    echo "Neither bison nor yacc was found."
    exit 1
fi

g++ -w -c -o y.o y.tab.c

if command -v flex >/dev/null 2>&1; then
    flex "$SOURCE_L"
elif command -v lex >/dev/null 2>&1; then
    lex "$SOURCE_L"
else
    echo "Neither flex nor lex was found."
    exit 1
fi

g++ -fpermissive -w -c -o l.o lex.yy.c
g++ y.o l.o -o parser.out
./parser.out "$INPUT_FILE"
