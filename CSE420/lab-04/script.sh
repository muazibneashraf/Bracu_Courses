#!/bin/bash
set -e

if command -v bison >/dev/null 2>&1; then
    bison -d -y --debug --verbose 21101177.y
elif command -v yacc >/dev/null 2>&1; then
    yacc -d 21101177.y
else
    echo "yacc/bison not found"
    exit 1
fi

echo 'Generated the parser C file and header file'
g++ -w -c -o y.o y.tab.c
echo 'Generated the parser object file'

if command -v flex >/dev/null 2>&1; then
    flex 21101177.l
elif command -v lex >/dev/null 2>&1; then
    lex 21101177.l
else
    echo "flex/lex not found"
    exit 1
fi

echo 'Generated the scanner C file'
g++ -fpermissive -w -c -o l.o lex.yy.c
echo 'Generated the scanner object file'
g++ y.o l.o -o two_pass_compiler
echo 'All ready, running the two-pass compiler...'

./two_pass_compiler input.c
echo 'Compilation completed.'

echo '------------ Log output ------------'
cat log.txt
echo '------------ Error output ------------'
cat error.txt
echo '------------ Three Address Code ------------'
cat code.txt
