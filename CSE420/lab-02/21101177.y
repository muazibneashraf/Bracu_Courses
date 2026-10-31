%{
#include <bits/stdc++.h>
#include "symbol_table.h"

#define YYSTYPE symbol_info*

using namespace std;

extern FILE *yyin;
int yyparse(void);
int yylex(void);
extern YYSTYPE yylval;

ofstream outlog;
int lines = 1;
symbol_table st(10, &outlog);

vector<pair<string, string> > pending_named_parameters;
bool pending_function_parameters = false;

void queue_named_parameters(symbol_info *info)
{
    pending_named_parameters.clear();
    pending_function_parameters = false;
    if (info == NULL) return;

    const vector<string> &types = info->get_parameter_types();
    const vector<string> &names = info->get_parameter_names();
    for (size_t i = 0; i < types.size(); i++)
    {
        if (!names[i].empty())
        {
            pending_named_parameters.push_back(make_pair(types[i], names[i]));
        }
    }
    pending_function_parameters = true;
}

void insert_pending_parameters()
{
    if (!pending_function_parameters) return;
    for (size_t i = 0; i < pending_named_parameters.size(); i++)
    {
        symbol_info *param = new symbol_info(pending_named_parameters[i].second, "ID");
        param->set_symbol_type("Variable");
        param->set_data_type(pending_named_parameters[i].first);
        st.insert(param);
    }
    pending_named_parameters.clear();
    pending_function_parameters = false;
}

void yyerror(char *s)
{
    outlog << "At line " << lines << " " << s << endl << endl;
}
%}

%token IF ELSE FOR WHILE DO BREAK INT CHAR FLOAT DOUBLE VOID RETURN SWITCH CASE DEFAULT CONTINUE PRINTLN ADDOP MULOP INCOP DECOP RELOP ASSIGNOP LOGICOP NOT LPAREN RPAREN LCURL RCURL LTHIRD RTHIRD COMMA SEMICOLON CONST_INT CONST_FLOAT ID

%nonassoc IFX
%nonassoc ELSE

%%

start : program
    {
        outlog << "At line no: " << lines << " start : program " << endl << endl;
        outlog << "Symbol Table" << endl << endl;
        st.print_all_scopes(outlog);
    }
    ;

program : program unit
    {
        outlog << "At line no: " << lines << " program : program unit " << endl << endl;
        outlog << $1->get_name() << "\n" << $2->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "\n" + $2->get_name(), "program");
    }
    | unit
    {
        outlog << "At line no: " << lines << " program : unit " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "program");
    }
    ;

unit : var_declaration
    {
        outlog << "At line no: " << lines << " unit : var_declaration " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "unit");
    }
    | func_definition
    {
        outlog << "At line no: " << lines << " unit : func_definition " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "unit");
    }
    ;

func_definition : type_specifier ID LPAREN parameter_list RPAREN
    {
        symbol_info *func = new symbol_info($2->get_name(), "ID");
        func->set_symbol_type("Function");
        func->set_data_type($1->get_name());
        func->copy_parameters_from($4);
        st.insert(func);
        queue_named_parameters($4);
    }
    compound_statement
    {
        outlog << "At line no: " << lines << " func_definition : type_specifier ID LPAREN parameter_list RPAREN compound_statement " << endl << endl;
        outlog << $1->get_name() << " " << $2->get_name() << "(" << $4->get_name() << ")\n" << $7->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + " " + $2->get_name() + "(" + $4->get_name() + ")\n" + $7->get_name(), "func_definition");
    }
    | type_specifier ID LPAREN RPAREN
    {
        symbol_info *func = new symbol_info($2->get_name(), "ID");
        func->set_symbol_type("Function");
        func->set_data_type($1->get_name());
        st.insert(func);
        pending_named_parameters.clear();
        pending_function_parameters = true;
    }
    compound_statement
    {
        outlog << "At line no: " << lines << " func_definition : type_specifier ID LPAREN RPAREN compound_statement " << endl << endl;
        outlog << $1->get_name() << " " << $2->get_name() << "()\n" << $6->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + " " + $2->get_name() + "()\n" + $6->get_name(), "func_definition");
    }
    ;

parameter_list : parameter_list COMMA type_specifier ID
    {
        outlog << "At line no: " << lines << " parameter_list : parameter_list COMMA type_specifier ID " << endl << endl;
        outlog << $1->get_name() << "," << $3->get_name() << " " << $4->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "," + $3->get_name() + " " + $4->get_name(), "parameter_list");
        $$->copy_parameters_from($1);
        $$->add_parameter($3->get_name(), $4->get_name());
    }
    | parameter_list COMMA type_specifier
    {
        outlog << "At line no: " << lines << " parameter_list : parameter_list COMMA type_specifier " << endl << endl;
        outlog << $1->get_name() << "," << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "," + $3->get_name(), "parameter_list");
        $$->copy_parameters_from($1);
        $$->add_parameter($3->get_name(), "");
    }
    | type_specifier ID
    {
        outlog << "At line no: " << lines << " parameter_list : type_specifier ID " << endl << endl;
        outlog << $1->get_name() << " " << $2->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + " " + $2->get_name(), "parameter_list");
        $$->add_parameter($1->get_name(), $2->get_name());
    }
    | type_specifier
    {
        outlog << "At line no: " << lines << " parameter_list : type_specifier " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "parameter_list");
        $$->add_parameter($1->get_name(), "");
    }
    ;

compound_statement : LCURL
    {
        st.enter_scope();
        insert_pending_parameters();
    }
    statements RCURL
    {
        outlog << "At line no: " << lines << " compound_statement : LCURL statements RCURL " << endl << endl;
        outlog << "{\n" << $3->get_name() << "\n}" << endl << endl;
        $$ = new symbol_info("{\n" + $3->get_name() + "\n}", "compound_statement");
        st.print_all_scopes(outlog);
        st.exit_scope();
    }
    | LCURL
    {
        st.enter_scope();
        insert_pending_parameters();
    }
    RCURL
    {
        outlog << "At line no: " << lines << " compound_statement : LCURL RCURL " << endl << endl;
        outlog << "{\n}" << endl << endl;
        $$ = new symbol_info("{\n}", "compound_statement");
        st.print_all_scopes(outlog);
        st.exit_scope();
    }
    ;

var_declaration : type_specifier declaration_list SEMICOLON
    {
        outlog << "At line no: " << lines << " var_declaration : type_specifier declaration_list SEMICOLON " << endl << endl;
        outlog << $1->get_name() << " " << $2->get_name() << ";" << endl << endl;
        $$ = new symbol_info($1->get_name() + " " + $2->get_name() + ";", "var_declaration");

        string declaration_text = $2->get_name();
        string token = "";
        for (size_t i = 0; i <= declaration_text.size(); i++)
        {
            if (i == declaration_text.size() || declaration_text[i] == ',')
            {
                if (!token.empty())
                {
                    symbol_info *var = NULL;
                    size_t left = token.find('[');
                    size_t right = token.find(']');
                    if (left != string::npos && right != string::npos)
                    {
                        var = new symbol_info(token.substr(0, left), "ID");
                        var->set_symbol_type("Array");
                        var->set_data_type($1->get_name());
                        var->set_array_size(atoi(token.substr(left + 1, right - left - 1).c_str()));
                    }
                    else
                    {
                        var = new symbol_info(token, "ID");
                        var->set_symbol_type("Variable");
                        var->set_data_type($1->get_name());
                    }
                    st.insert(var);
                }
                token.clear();
            }
            else
            {
                token.push_back(declaration_text[i]);
            }
        }
    }
    ;

type_specifier : INT
    {
        outlog << "At line no: " << lines << " type_specifier : INT " << endl << endl;
        outlog << "int" << endl << endl;
        $$ = new symbol_info("int", "type_specifier");
    }
    | FLOAT
    {
        outlog << "At line no: " << lines << " type_specifier : FLOAT " << endl << endl;
        outlog << "float" << endl << endl;
        $$ = new symbol_info("float", "type_specifier");
    }
    | VOID
    {
        outlog << "At line no: " << lines << " type_specifier : VOID " << endl << endl;
        outlog << "void" << endl << endl;
        $$ = new symbol_info("void", "type_specifier");
    }
    ;

declaration_list : declaration_list COMMA ID
    {
        outlog << "At line no: " << lines << " declaration_list : declaration_list COMMA ID " << endl << endl;
        outlog << $1->get_name() << "," << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "," + $3->get_name(), "declaration_list");
    }
    | declaration_list COMMA ID LTHIRD CONST_INT RTHIRD
    {
        outlog << "At line no: " << lines << " declaration_list : declaration_list COMMA ID LTHIRD CONST_INT RTHIRD " << endl << endl;
        outlog << $1->get_name() << "," << $3->get_name() << "[" << $5->get_name() << "]" << endl << endl;
        $$ = new symbol_info($1->get_name() + "," + $3->get_name() + "[" + $5->get_name() + "]", "declaration_list");
    }
    | ID
    {
        outlog << "At line no: " << lines << " declaration_list : ID " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "declaration_list");
    }
    | ID LTHIRD CONST_INT RTHIRD
    {
        outlog << "At line no: " << lines << " declaration_list : ID LTHIRD CONST_INT RTHIRD " << endl << endl;
        outlog << $1->get_name() << "[" << $3->get_name() << "]" << endl << endl;
        $$ = new symbol_info($1->get_name() + "[" + $3->get_name() + "]", "declaration_list");
    }
    ;

statements : statement
    {
        outlog << "At line no: " << lines << " statements : statement " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "statements");
    }
    | statements statement
    {
        outlog << "At line no: " << lines << " statements : statements statement " << endl << endl;
        outlog << $1->get_name() << "\n" << $2->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "\n" + $2->get_name(), "statements");
    }
    ;

statement : var_declaration
    {
        outlog << "At line no: " << lines << " statement : var_declaration " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "statement");
    }
    | expression_statement
    {
        outlog << "At line no: " << lines << " statement : expression_statement " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "statement");
    }
    | compound_statement
    {
        outlog << "At line no: " << lines << " statement : compound_statement " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "statement");
    }
    | FOR LPAREN expression_statement expression_statement expression RPAREN statement
    {
        outlog << "At line no: " << lines << " statement : FOR LPAREN expression_statement expression_statement expression RPAREN statement " << endl << endl;
        outlog << "for(" << $3->get_name() << $4->get_name() << $5->get_name() << ")\n" << $7->get_name() << endl << endl;
        $$ = new symbol_info("for(" + $3->get_name() + $4->get_name() + $5->get_name() + ")\n" + $7->get_name(), "statement");
    }
    | IF LPAREN expression RPAREN statement %prec IFX
    {
        outlog << "At line no: " << lines << " statement : IF LPAREN expression RPAREN statement " << endl << endl;
        outlog << "if(" << $3->get_name() << ")\n" << $5->get_name() << endl << endl;
        $$ = new symbol_info("if(" + $3->get_name() + ")\n" + $5->get_name(), "statement");
    }
    | IF LPAREN expression RPAREN statement ELSE statement
    {
        outlog << "At line no: " << lines << " statement : IF LPAREN expression RPAREN statement ELSE statement " << endl << endl;
        outlog << "if(" << $3->get_name() << ")\n" << $5->get_name() << "\nelse\n" << $7->get_name() << endl << endl;
        $$ = new symbol_info("if(" + $3->get_name() + ")\n" + $5->get_name() + "\nelse\n" + $7->get_name(), "statement");
    }
    | WHILE LPAREN expression RPAREN statement
    {
        outlog << "At line no: " << lines << " statement : WHILE LPAREN expression RPAREN statement " << endl << endl;
        outlog << "while(" << $3->get_name() << ")\n" << $5->get_name() << endl << endl;
        $$ = new symbol_info("while(" + $3->get_name() + ")\n" + $5->get_name(), "statement");
    }
    | PRINTLN LPAREN ID RPAREN SEMICOLON
    {
        outlog << "At line no: " << lines << " statement : PRINTLN LPAREN ID RPAREN SEMICOLON " << endl << endl;
        outlog << "printf(" << $3->get_name() << ");" << endl << endl;
        $$ = new symbol_info("printf(" + $3->get_name() + ");", "statement");
    }
    | RETURN expression SEMICOLON
    {
        outlog << "At line no: " << lines << " statement : RETURN expression SEMICOLON " << endl << endl;
        outlog << "return " << $2->get_name() << ";" << endl << endl;
        $$ = new symbol_info("return " + $2->get_name() + ";", "statement");
    }
    ;

expression_statement : SEMICOLON
    {
        outlog << "At line no: " << lines << " expression_statement : SEMICOLON " << endl << endl;
        outlog << ";" << endl << endl;
        $$ = new symbol_info(";", "expression_statement");
    }
    | expression SEMICOLON
    {
        outlog << "At line no: " << lines << " expression_statement : expression SEMICOLON " << endl << endl;
        outlog << $1->get_name() << ";" << endl << endl;
        $$ = new symbol_info($1->get_name() + ";", "expression_statement");
    }
    ;

variable : ID
    {
        outlog << "At line no: " << lines << " variable : ID " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "variable");
    }
    | ID LTHIRD expression RTHIRD
    {
        outlog << "At line no: " << lines << " variable : ID LTHIRD expression RTHIRD " << endl << endl;
        outlog << $1->get_name() << "[" << $3->get_name() << "]" << endl << endl;
        $$ = new symbol_info($1->get_name() + "[" + $3->get_name() + "]", "variable");
    }
    ;

expression : logic_expression
    {
        outlog << "At line no: " << lines << " expression : logic_expression " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "expression");
    }
    | variable ASSIGNOP logic_expression
    {
        outlog << "At line no: " << lines << " expression : variable ASSIGNOP logic_expression " << endl << endl;
        outlog << $1->get_name() << "=" << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "=" + $3->get_name(), "expression");
    }
    ;

logic_expression : rel_expression
    {
        outlog << "At line no: " << lines << " logic_expression : rel_expression " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "logic_expression");
    }
    | rel_expression LOGICOP rel_expression
    {
        outlog << "At line no: " << lines << " logic_expression : rel_expression LOGICOP rel_expression " << endl << endl;
        outlog << $1->get_name() << $2->get_name() << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + $2->get_name() + $3->get_name(), "logic_expression");
    }
    ;

rel_expression : simple_expression
    {
        outlog << "At line no: " << lines << " rel_expression : simple_expression " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "rel_expression");
    }
    | simple_expression RELOP simple_expression
    {
        outlog << "At line no: " << lines << " rel_expression : simple_expression RELOP simple_expression " << endl << endl;
        outlog << $1->get_name() << $2->get_name() << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + $2->get_name() + $3->get_name(), "rel_expression");
    }
    ;

simple_expression : term
    {
        outlog << "At line no: " << lines << " simple_expression : term " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "simple_expression");
    }
    | simple_expression ADDOP term
    {
        outlog << "At line no: " << lines << " simple_expression : simple_expression ADDOP term " << endl << endl;
        outlog << $1->get_name() << $2->get_name() << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + $2->get_name() + $3->get_name(), "simple_expression");
    }
    ;

term : unary_expression
    {
        outlog << "At line no: " << lines << " term : unary_expression " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "term");
    }
    | term MULOP unary_expression
    {
        outlog << "At line no: " << lines << " term : term MULOP unary_expression " << endl << endl;
        outlog << $1->get_name() << $2->get_name() << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + $2->get_name() + $3->get_name(), "term");
    }
    ;

unary_expression : ADDOP unary_expression
    {
        outlog << "At line no: " << lines << " unary_expression : ADDOP unary_expression " << endl << endl;
        outlog << $1->get_name() << $2->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + $2->get_name(), "unary_expression");
    }
    | NOT unary_expression
    {
        outlog << "At line no: " << lines << " unary_expression : NOT unary_expression " << endl << endl;
        outlog << "!" << $2->get_name() << endl << endl;
        $$ = new symbol_info("!" + $2->get_name(), "unary_expression");
    }
    | factor
    {
        outlog << "At line no: " << lines << " unary_expression : factor " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "unary_expression");
    }
    ;

factor : variable
    {
        outlog << "At line no: " << lines << " factor : variable " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "factor");
    }
    | ID LPAREN argument_list RPAREN
    {
        outlog << "At line no: " << lines << " factor : ID LPAREN argument_list RPAREN " << endl << endl;
        outlog << $1->get_name() << "(" << $3->get_name() << ")" << endl << endl;
        $$ = new symbol_info($1->get_name() + "(" + $3->get_name() + ")", "factor");
    }
    | LPAREN expression RPAREN
    {
        outlog << "At line no: " << lines << " factor : LPAREN expression RPAREN " << endl << endl;
        outlog << "(" << $2->get_name() << ")" << endl << endl;
        $$ = new symbol_info("(" + $2->get_name() + ")", "factor");
    }
    | CONST_INT
    {
        outlog << "At line no: " << lines << " factor : CONST_INT " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "factor");
    }
    | CONST_FLOAT
    {
        outlog << "At line no: " << lines << " factor : CONST_FLOAT " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "factor");
    }
    | variable INCOP
    {
        outlog << "At line no: " << lines << " factor : variable INCOP " << endl << endl;
        outlog << $1->get_name() << "++" << endl << endl;
        $$ = new symbol_info($1->get_name() + "++", "factor");
    }
    | variable DECOP
    {
        outlog << "At line no: " << lines << " factor : variable DECOP " << endl << endl;
        outlog << $1->get_name() << "--" << endl << endl;
        $$ = new symbol_info($1->get_name() + "--", "factor");
    }
    ;

argument_list : arguments
    {
        outlog << "At line no: " << lines << " argument_list : arguments " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "argument_list");
    }
    |
    {
        outlog << "At line no: " << lines << " argument_list :  " << endl << endl;
        outlog << "" << endl << endl;
        $$ = new symbol_info("", "argument_list");
    }
    ;

arguments : arguments COMMA logic_expression
    {
        outlog << "At line no: " << lines << " arguments : arguments COMMA logic_expression " << endl << endl;
        outlog << $1->get_name() << "," << $3->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name() + "," + $3->get_name(), "arguments");
    }
    | logic_expression
    {
        outlog << "At line no: " << lines << " arguments : logic_expression " << endl << endl;
        outlog << $1->get_name() << endl << endl;
        $$ = new symbol_info($1->get_name(), "arguments");
    }
    ;

%%

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        cout << "Please input file name" << endl;
        return 0;
    }

    yyin = fopen(argv[1], "r");
    outlog.open("21101177_log.txt", ios::trunc);
    st.enter_scope();

    if (yyin == NULL)
    {
        cout << "Couldn't open file" << endl;
        return 0;
    }

    yyparse();
    outlog << "Total lines: " << lines << endl;
    outlog.close();
    fclose(yyin);
    return 0;
}
