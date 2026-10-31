%option noyywrap

%{
#include <bits/stdc++.h>
#include "symbol_info.h"

#define YYSTYPE symbol_info*

#include "y.tab.h"

extern YYSTYPE yylval;
extern int lines;

void yyerror(char *);
using namespace std;
%}

delim      [ \t\v\r\f]
newline    \r?\n
ws         {delim}+
letter_    [A-Za-z_]
digit      [0-9]
id         {letter_}({letter_}|{digit})*
integers   {digit}+
floats     ({digit}+\.{digit}*|{digit}*\.{digit}+)((E|e)[+-]?{digit}+)?

%%

{ws}            { }
{newline}       { lines++; }

if              { return IF; }
else            { return ELSE; }
for             { return FOR; }
while           { return WHILE; }
do              { return DO; }
break           { return BREAK; }
continue        { return CONTINUE; }
return          { return RETURN; }
int             { return INT; }
float           { return FLOAT; }
char            { return CHAR; }
void            { return VOID; }
double          { return DOUBLE; }
switch          { return SWITCH; }
case            { return CASE; }
default         { return DEFAULT; }
printf          { return PRINTLN; }

"++"            { return INCOP; }
"--"            { return DECOP; }
"+"|"-"         { yylval = new symbol_info((string)yytext, "ADDOP"); return ADDOP; }
"*"|"/"|"%"     { yylval = new symbol_info((string)yytext, "MULOP"); return MULOP; }
"<"|">"|"<="|">="|"=="|"!=" { yylval = new symbol_info((string)yytext, "RELOP"); return RELOP; }
"="             { return ASSIGNOP; }
"&&"|"||"       { yylval = new symbol_info((string)yytext, "LOGICOP"); return LOGICOP; }
"!"             { return NOT; }
"("             { return LPAREN; }
")"             { return RPAREN; }
"{"             { return LCURL; }
"}"             { return RCURL; }
"["             { return LTHIRD; }
"]"             { return RTHIRD; }
";"             { return SEMICOLON; }
","             { return COMMA; }

{id}            { yylval = new symbol_info((string)yytext, "ID"); return ID; }
{integers}      { yylval = new symbol_info((string)yytext, "CONST_INT"); return CONST_INT; }
{floats}        { yylval = new symbol_info((string)yytext, "CONST_FLOAT"); return CONST_FLOAT; }

.               { }

%%
