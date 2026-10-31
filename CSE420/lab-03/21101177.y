%{

#include "symbol_table.h"

#define YYSTYPE symbol_info*
#include <string>
#include <cstring>
#include <sstream>
#include <cctype>

extern FILE *yyin;
int yyparse(void);
int yylex(void);

extern YYSTYPE yylval;

symbol_table *table;

int lines = 1;
ofstream outlog;
ofstream errorlog;
int error_count = 0;

string current_type;
string current_func_name;
vector<pair<string,string> > current_func_params;
vector<string> pending_decl_errors;

void yyerror(char *s)
{
    outlog << "Error at line " << lines << ": " << s << endl << endl;
}

void report_semantic_error(const string& message)
{
    outlog << "At line no: " << lines << " " << message << endl << endl;
    errorlog << "At line no: " << lines << " " << message << endl << endl;
    error_count++;
}

symbol_info* lookup_symbol(const string& name)
{
    symbol_info temp(name, "ID");
    return table->lookup(&temp);
}

symbol_info* lookup_current_scope_symbol(const string& name)
{
    symbol_info temp(name, "ID");
    return table->lookup_current_scope(&temp);
}

bool is_variable_declared_current_scope(const string& name)
{
    return lookup_current_scope_symbol(name) != NULL;
}

bool is_function_declared(const string& name)
{
    symbol_info* found = lookup_symbol(name);
    return found != NULL && found->get_is_function();
}

%}

%token IF ELSE FOR WHILE DO BREAK INT CHAR FLOAT DOUBLE VOID RETURN SWITCH CASE DEFAULT CONTINUE PRINTLN ADDOP MULOP INCOP DECOP RELOP ASSIGNOP LOGICOP NOT LPAREN RPAREN LCURL RCURL LTHIRD RTHIRD COMMA SEMICOLON CONST_INT CONST_FLOAT ID

%nonassoc LOWER_THAN_ELSE
%nonassoc ELSE

%%

start : program
	{
		outlog<<"At line no: "<<lines<<" start : program "<<endl<<endl;
		outlog<<"Symbol Table"<<endl<<endl;
		
		// Print your whole symbol table here
		table->print_all_scopes(outlog);
	}
	;

program : program unit
	{
		outlog<<"At line no: "<<lines<<" program : program unit "<<endl<<endl;
		outlog<<$1->getname()+"\n"+$2->getname()<<endl<<endl;
		
		$$ = new symbol_info($1->getname()+"\n"+$2->getname(),"program");
	}
	| unit
	{
		outlog<<"At line no: "<<lines<<" program : unit "<<endl<<endl;
		outlog<<$1->getname()<<endl<<endl;
		
		$$ = new symbol_info($1->getname(),"program");
	}
	;

unit : var_declaration
	 {
		outlog<<"At line no: "<<lines<<" unit : var_declaration "<<endl<<endl;
		outlog<<$1->getname()<<endl<<endl;
		
		$$ = new symbol_info($1->getname(),"unit");
	 }
     | func_definition
     {
		outlog<<"At line no: "<<lines<<" unit : func_definition "<<endl<<endl;
		outlog<<$1->getname()<<endl<<endl;
		
		$$ = new symbol_info($1->getname(),"unit");
	 }
     ;

func_definition : type_specifier ID LPAREN
        {
            current_func_name = $2->getname();
            current_func_params.clear();
        }
        parameter_list RPAREN
        {
            if (lookup_current_scope_symbol($2->getname()) != NULL) {
                report_semantic_error("Multiple declaration of function " + $2->getname());
            } else {
                vector<pair<string, string> > params = current_func_params;
                symbol_info* func = new symbol_info($2->getname(), "ID", $1->getname());
                func->set_as_function($1->getname(), params);
                table->insert(func);
            }
        }
        compound_statement
        {
            outlog<<"At line no: "<<lines<<" func_definition : type_specifier ID LPAREN parameter_list RPAREN compound_statement "<<endl<<endl;
            outlog<<$1->getname()<<" "<<$2->getname()<<"("+$5->getname()+")\n"<<$8->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+" "+$2->getname()+"("+$5->getname()+")\n"+$8->getname(),"func_def");
            current_func_params.clear();
        }
        | type_specifier ID LPAREN
        {
            current_func_name = $2->getname();
            current_func_params.clear();
        }
        RPAREN
        {
            if (lookup_current_scope_symbol($2->getname()) != NULL) {
                report_semantic_error("Multiple declaration of function " + $2->getname());
            } else {
                vector<pair<string, string> > params;
                symbol_info* func = new symbol_info($2->getname(), "ID", $1->getname());
                func->set_as_function($1->getname(), params);
                table->insert(func);
            }
        }
        compound_statement
        {
            outlog<<"At line no: "<<lines<<" func_definition : type_specifier ID LPAREN RPAREN compound_statement "<<endl<<endl;
            outlog<<$1->getname()<<" "<<$2->getname()<<"()\n"<<$7->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+" "+$2->getname()+"()\n"+$7->getname(),"func_def");
            current_func_params.clear();
        }
        ;

parameter_list : parameter_list COMMA type_specifier ID
        {
            outlog<<"At line no: "<<lines<<" parameter_list : parameter_list COMMA type_specifier ID "<<endl<<endl;
            outlog<<$1->getname()<<","<<$3->getname()<<" "<<$4->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+","+$3->getname()+" "+$4->getname(),"param_list");

            for (auto &param : current_func_params) {
                if (!param.second.empty() && param.second == $4->getname()) {
                    report_semantic_error("Multiple declaration of variable " + $4->getname() + " in parameter of " + current_func_name);
                    break;
                }
            }

            pair<string, string> param($3->getname(), $4->getname());
            current_func_params.push_back(param);
        }
        | parameter_list COMMA type_specifier
        {
            outlog<<"At line no: "<<lines<<" parameter_list : parameter_list COMMA type_specifier "<<endl<<endl;
            outlog<<$1->getname()<<","<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+","+$3->getname(),"param_list");

            pair<string, string> param($3->getname(), "");
            current_func_params.push_back(param);
        }
        | type_specifier ID
        {
            outlog<<"At line no: "<<lines<<" parameter_list : type_specifier ID "<<endl<<endl;
            outlog<<$1->getname()<<" "<<$2->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+" "+$2->getname(),"param_list");

            pair<string, string> param($1->getname(), $2->getname());
            current_func_params.push_back(param);
        }
        | type_specifier
        {
            outlog<<"At line no: "<<lines<<" parameter_list : type_specifier "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"param_list");

            pair<string, string> param($1->getname(), "");
            current_func_params.push_back(param);
        }
        ;

compound_statement : LCURL {

			table->enter_scope();
		
			if(!current_func_params.empty()) {
				for(auto param : current_func_params) {
					if(!param.second.empty()) {
						symbol_info* param_symbol = new symbol_info(param.second, "ID", param.first);
						table->insert(param_symbol);
					}
				}
				current_func_params.clear();
			}
		
		
		
		
		} statements RCURL
			{ 
 		    	outlog<<"At line no: "<<lines<<" compound_statement : LCURL statements RCURL "<<endl<<endl;
				outlog<<"{\n"+$3->getname()+"\n}"<<endl<<endl;
				
				table->print_current_scope();
		

				table->exit_scope();
				$$ = new symbol_info("{\n"+$3->getname()+"\n}","comp_stmnt");
 		    }

 		    | LCURL {
				table->enter_scope();

			}
			
			RCURL
 		    { 
 		    	outlog<<"At line no: "<<lines<<" compound_statement : LCURL RCURL "<<endl<<endl;
				outlog<<"{\n}"<<endl<<endl;
				
				
				
				// The compound statement is complete.
                // Print the symbol table here and exit the scope
				table->print_current_scope();

				table->exit_scope();

				$$ = new symbol_info("{\n}","comp_stmnt");
 		    }
 		    ;
 		    
var_declaration : type_specifier declaration_list SEMICOLON
         {
            outlog<<"At line no: "<<lines<<" var_declaration : type_specifier declaration_list SEMICOLON "<<endl<<endl;
            outlog<<$1->getname()<<" "<<$2->getname()<<";"<<endl<<endl;

            $$ = new symbol_info($1->getname()+" "+$2->getname() + ";","var_dec");

            if($1->getname() == "void") {
                report_semantic_error("variable type can not be void ");
            }

            for (const string& msg : pending_decl_errors) {
                report_semantic_error(msg);
            }
            pending_decl_errors.clear();
         }
         ;

type_specifier : INT
		{
			outlog<<"At line no: "<<lines<<" type_specifier : INT "<<endl<<endl;
			outlog<<"int"<<endl<<endl;
			
			$$ = new symbol_info("int","type");
			current_type = "int";
	    }
 		| FLOAT
 		{
			outlog<<"At line no: "<<lines<<" type_specifier : FLOAT "<<endl<<endl;
			outlog<<"float"<<endl<<endl;
			
			$$ = new symbol_info("float","type");
			current_type = "float";
	    }
 		| VOID
 		{
			outlog<<"At line no: "<<lines<<" type_specifier : VOID "<<endl<<endl;
			outlog<<"void"<<endl<<endl;
			
			$$ = new symbol_info("void","type");
			current_type = "void";
	    }
 		;

declaration_list : declaration_list COMMA ID
          {
            outlog<<"At line no: "<<lines<<" declaration_list : declaration_list COMMA ID "<<endl<<endl;
            outlog<<$1->getname()+","<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname() + "," + $3->getname(), "decl_list");
            if(is_variable_declared_current_scope($3->getname())) {
                pending_decl_errors.push_back("Multiple declaration of variable " + $3->getname());
            } else {
                string insert_type = (current_type == "void") ? "error" : current_type;
                symbol_info* new_var = new symbol_info($3->getname(), "ID", insert_type);
                table->insert(new_var);
            }
          }
          | declaration_list COMMA ID LTHIRD CONST_INT RTHIRD
          {
            outlog<<"At line no: "<<lines<<" declaration_list : declaration_list COMMA ID LTHIRD CONST_INT RTHIRD "<<endl<<endl;
            outlog<<$1->getname()+","<<$3->getname()<<"["<<$5->getname()<<"]"<<endl<<endl;

            $$ = new symbol_info($1->getname() + "," + $3->getname() + "[" + $5->getname() + "]", "decl_list");
            if(is_variable_declared_current_scope($3->getname())) {
                pending_decl_errors.push_back("Multiple declaration of variable " + $3->getname());
            } else {
                int size = stoi($5->getname());
                string insert_type = (current_type == "void") ? "error" : current_type;
                symbol_info* new_array = new symbol_info($3->getname(), "ID", insert_type, size);
                table->insert(new_array);
            }
          }
          | ID
          {
            outlog<<"At line no: "<<lines<<" declaration_list : ID "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(), "decl_list");
            if(is_variable_declared_current_scope($1->getname())) {
                pending_decl_errors.push_back("Multiple declaration of variable " + $1->getname());
            } else {
                string insert_type = (current_type == "void") ? "error" : current_type;
                symbol_info* new_var = new symbol_info($1->getname(), "ID", insert_type);
                table->insert(new_var);
            }
          }
          | ID LTHIRD CONST_INT RTHIRD
          {
            outlog<<"At line no: "<<lines<<" declaration_list : ID LTHIRD CONST_INT RTHIRD "<<endl<<endl;
            outlog<<$1->getname()<<"["<<$3->getname()<<"]"<<endl<<endl;

            $$ = new symbol_info($1->getname() + "[" + $3->getname() + "]", "decl_list");
            if(is_variable_declared_current_scope($1->getname())) {
                pending_decl_errors.push_back("Multiple declaration of variable " + $1->getname());
            } else {
                int size = stoi($3->getname());
                string insert_type = (current_type == "void") ? "error" : current_type;
                symbol_info* new_array = new symbol_info($1->getname(), "ID", insert_type, size);
                table->insert(new_array);
            }
          }
          ;
 		  

statements : statement
	   {
	    	outlog<<"At line no: "<<lines<<" statements : statement "<<endl<<endl;
			outlog<<$1->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname(),"stmnts");
	   }
	   | statements statement
	   {
	    	outlog<<"At line no: "<<lines<<" statements : statements statement "<<endl<<endl;
			outlog<<$1->getname()<<"\n"<<$2->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname()+"\n"+$2->getname(),"stmnts");
	   }
	   ;
	   
statement : var_declaration
	  {
	    	outlog<<"At line no: "<<lines<<" statement : var_declaration "<<endl<<endl;
			outlog<<$1->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname(),"stmnt");
	  }
	  | func_definition
	  {
	  		outlog<<"At line no: "<<lines<<" statement : func_definition "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"stmnt");
	  		
	  }
	  | expression_statement
	  {
	    	outlog<<"At line no: "<<lines<<" statement : expression_statement "<<endl<<endl;
			outlog<<$1->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname(),"stmnt");
	  }
	  | compound_statement
	  {
	    	outlog<<"At line no: "<<lines<<" statement : compound_statement "<<endl<<endl;
			outlog<<$1->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname(),"stmnt");
	  }
	  | FOR LPAREN expression_statement expression_statement expression RPAREN statement
	  {
	    	outlog<<"At line no: "<<lines<<" statement : FOR LPAREN expression_statement expression_statement expression RPAREN statement "<<endl<<endl;
			outlog<<"for("<<$3->getname()<<$4->getname()<<$5->getname()<<")\n"<<$7->getname()<<endl<<endl;
			
			$$ = new symbol_info("for("+$3->getname()+$4->getname()+$5->getname()+")\n"+$7->getname(),"stmnt");
	  }
	  | IF LPAREN expression RPAREN statement %prec LOWER_THAN_ELSE
	  {
	    	outlog<<"At line no: "<<lines<<" statement : IF LPAREN expression RPAREN statement "<<endl<<endl;
			outlog<<"if("<<$3->getname()<<")\n"<<$5->getname()<<endl<<endl;
			
			$$ = new symbol_info("if("+$3->getname()+")\n"+$5->getname(),"stmnt");
	  }
	  | IF LPAREN expression RPAREN statement ELSE statement
	  {
	    	outlog<<"At line no: "<<lines<<" statement : IF LPAREN expression RPAREN statement ELSE statement "<<endl<<endl;
			outlog<<"if("<<$3->getname()<<")\n"<<$5->getname()<<"\nelse\n"<<$7->getname()<<endl<<endl;
			
			$$ = new symbol_info("if("+$3->getname()+")\n"+$5->getname()+"\nelse\n"+$7->getname(),"stmnt");
	  }
	  | WHILE LPAREN expression RPAREN statement
	  {
	    	outlog<<"At line no: "<<lines<<" statement : WHILE LPAREN expression RPAREN statement "<<endl<<endl;
			outlog<<"while("<<$3->getname()<<")\n"<<$5->getname()<<endl<<endl;
			
			$$ = new symbol_info("while("+$3->getname()+")\n"+$5->getname(),"stmnt");
	  }
	  | PRINTLN LPAREN ID RPAREN SEMICOLON //edit
	  {
	    	outlog<<"At line no: "<<lines<<" statement : PRINTLN LPAREN ID RPAREN SEMICOLON "<<endl<<endl;
			outlog<<"printf("<<$3->getname()<<");"<<endl<<endl; 
			symbol_info* sym = table->lookup($3);
			if(sym == NULL) {
				errorlog << "At line no: " << lines << " Undeclared variable " << $3->getname() << endl << endl;
				error_count++;
			}
			$$ = new symbol_info("printf("+$3->getname()+");","stmnt");
	  }
	  | RETURN expression SEMICOLON 
	  {
	    	outlog<<"At line no: "<<lines<<" statement : RETURN expression SEMICOLON "<<endl<<endl;
			outlog<<"return "<<$2->getname()<<";"<<endl<<endl;
			
			$$ = new symbol_info("return "+$2->getname()+";","stmnt");
	  }
	  ;
	  
expression_statement : SEMICOLON
			{
				outlog<<"At line no: "<<lines<<" expression_statement : SEMICOLON "<<endl<<endl;
				outlog<<";"<<endl<<endl;
				
				$$ = new symbol_info(";","expr_stmt");
	        }			
			| expression SEMICOLON 
			{
				outlog<<"At line no: "<<lines<<" expression_statement : expression SEMICOLON "<<endl<<endl;
				outlog<<$1->getname()<<";"<<endl<<endl;
				
				$$ = new symbol_info($1->getname()+";","expr_stmt");
	        }
			;
	    
variable : ID
      {
        outlog<<"At line no: "<<lines<<" variable : ID "<<endl<<endl;
        outlog<<$1->getname()<<endl<<endl;

        $$ = new symbol_info($1->getname(),"varbl");
        symbol_info* sym = lookup_symbol($1->getname());
        if (sym == NULL) {
            report_semantic_error("Undeclared variable " + $1->getname());
            $$->set_data_type("error");
        } else if (sym->get_is_array()) {
            report_semantic_error("variable is of array type : " + $1->getname());
            $$->set_data_type("error");
        } else {
            $$->set_data_type(sym->get_data_type());
        }
     }
     | ID LTHIRD expression RTHIRD
     {
        outlog<<"At line no: "<<lines<<" variable : ID LTHIRD expression RTHIRD "<<endl<<endl;
        outlog<<$1->getname()<<"["<<$3->getname()<<"]"<<endl<<endl;

        $$ = new symbol_info($1->getname()+"["+$3->getname()+"]","varbl");
        symbol_info* sym = lookup_symbol($1->getname());
        if (sym == NULL) {
            report_semantic_error("Undeclared variable " + $1->getname());
            $$->set_data_type("error");
        } else if (!sym->get_is_array()) {
            report_semantic_error("variable is not of array type : " + $1->getname());
            $$->set_data_type("error");
        } else {
            $$->set_data_type(sym->get_data_type());
        }

        if($3->get_data_type() != "int" && $3->get_data_type() != "error") {
            report_semantic_error("array index is not of integer type : " + $1->getname());
            $$->set_data_type("error");
        } else if ($3->get_data_type() == "error") {
            $$->set_data_type("error");
        }
     }
     ;
	 
expression : logic_expression
       {
            outlog<<"At line no: "<<lines<<" expression : logic_expression "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"expr");
            $$->set_data_type($1->get_data_type());
       }
       | variable ASSIGNOP logic_expression
       {
            outlog<<"At line no: "<<lines<<" expression : variable ASSIGNOP logic_expression "<<endl<<endl;
            outlog<<$1->getname()<<"="<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+"="+$3->getname(),"expr");
            $$->set_data_type($1->get_data_type());

            if ($1->get_data_type() == "error" || $3->get_data_type() == "error") {
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "void" || $3->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "int" && $3->get_data_type() == "float") {
                report_semantic_error("Warning: Assignment of float value into variable of integer type ");
            }
       }
       ;
			
logic_expression : rel_expression
         {
            outlog<<"At line no: "<<lines<<" logic_expression : rel_expression "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"lgc_expr");
            $$->set_data_type($1->get_data_type());
         }
         | rel_expression LOGICOP rel_expression
         {
            outlog<<"At line no: "<<lines<<" logic_expression : rel_expression LOGICOP rel_expression "<<endl<<endl;
            outlog<<$1->getname()<<$2->getname()<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+$2->getname()+$3->getname(),"lgc_expr");
            if ($1->get_data_type() == "error" || $3->get_data_type() == "error") {
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "void" || $3->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else {
                $$->set_data_type("int");
            }
         }
         ;

rel_expression    : simple_expression
        {
            outlog<<"At line no: "<<lines<<" rel_expression : simple_expression "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"rel_expr");
            $$->set_data_type($1->get_data_type());
        }
        | simple_expression RELOP simple_expression
        {
            outlog<<"At line no: "<<lines<<" rel_expression : simple_expression RELOP simple_expression "<<endl<<endl;
            outlog<<$1->getname()<<$2->getname()<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+$2->getname()+$3->getname(),"rel_expr");
            if ($1->get_data_type() == "error" || $3->get_data_type() == "error") {
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "void" || $3->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else {
                $$->set_data_type("int");
            }
        }
        ;
				
simple_expression : term //edit
          {
	    	outlog<<"At line no: "<<lines<<" simple_expression : term "<<endl<<endl;
			outlog<<$1->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname(),"simp_expr");
			$$->set_data_type($1->get_data_type());
			
	      }
		  | simple_expression ADDOP term 
		  {
	    	outlog<<"At line no: "<<lines<<" simple_expression : simple_expression ADDOP term "<<endl<<endl;
			outlog<<$1->getname()<<$2->getname()<<$3->getname()<<endl<<endl;
			
			$$ = new symbol_info($1->getname()+$2->getname()+$3->getname(),"simp_expr");
            if ($1->get_data_type() == "error" || $3->get_data_type() == "error") {
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "void" || $3->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else if ($1->get_data_type() == "float" || $3->get_data_type() == "float") {
                $$->set_data_type("float");
            } else {
                $$->set_data_type("int");
            }
	      }
		  ;
					
term :   unary_expression
     {
            outlog<<"At line no: "<<lines<<" term : unary_expression "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"term");
            $$->set_data_type($1->get_data_type());
     }
     |  term MULOP unary_expression
     {
            outlog<<"At line no: "<<lines<<" term : term MULOP unary_expression "<<endl<<endl;
            outlog<<$1->getname()<<$2->getname()<<$3->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+$2->getname()+$3->getname(),"term");

            if ($1->get_data_type() == "error" || $3->get_data_type() == "error") {
                $$->set_data_type("error");
            }
            else if ($1->get_data_type() == "void" || $3->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            }
            else if ($2->getname() == "%") {
                if ($1->get_data_type() != "int" || $3->get_data_type() != "int") {
                    report_semantic_error("Modulus operator on non integer type ");
                }
                if ($3->getname() == "0") {
                    report_semantic_error("Modulus by 0 ");
                }
                $$->set_data_type("int");
            }
            else {
                if ($2->getname() == "/" && $3->getname() == "0") {
                    report_semantic_error("Division by 0 ");
                }
                if ($1->get_data_type() == "float" || $3->get_data_type() == "float")
                    $$->set_data_type("float");
                else
                    $$->set_data_type("int");
            }
     }
     ;

unary_expression : ADDOP unary_expression
         {
            outlog<<"At line no: "<<lines<<" unary_expression : ADDOP unary_expression "<<endl<<endl;
            outlog<<$1->getname()<<$2->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname()+$2->getname(),"un_expr");
            if ($2->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else {
                $$->set_data_type($2->get_data_type());
            }
         }
         | NOT unary_expression
         {
            outlog<<"At line no: "<<lines<<" unary_expression : NOT unary_expression "<<endl<<endl;
            outlog<<"!"<<$2->getname()<<endl<<endl;

            $$ = new symbol_info("!"+$2->getname(),"un_expr");
            if ($2->get_data_type() == "void") {
                report_semantic_error("operation on void type ");
                $$->set_data_type("error");
            } else if ($2->get_data_type() == "error") {
                $$->set_data_type("error");
            } else {
                $$->set_data_type("int");
            }
         }
         | factor
         {
            outlog<<"At line no: "<<lines<<" unary_expression : factor "<<endl<<endl;
            outlog<<$1->getname()<<endl<<endl;

            $$ = new symbol_info($1->getname(),"un_expr");
            $$->set_data_type($1->get_data_type());
         }
         ;
	
factor  : variable
    {
        outlog<<"At line no: "<<lines<<" factor : variable "<<endl<<endl;
        outlog<<$1->getname()<<endl<<endl;

        $$ = new symbol_info($1->getname(),"fctr");
        $$->set_data_type($1->get_data_type());
    }
    | ID LPAREN argument_list RPAREN
    {
        outlog<<"At line no: "<<lines<<" factor : ID LPAREN argument_list RPAREN "<<endl<<endl;
        outlog<<$1->getname()<<"("<<$3->getname()<<")"<<endl<<endl;

        symbol_info* func = lookup_symbol($1->getname());
        $$ = new symbol_info($1->getname()+"("+$3->getname()+")","fctr");

        if (!func) {
            report_semantic_error("Undeclared function: " + $1->getname());
            $$->set_data_type("error");
        } else if (!func->get_is_function()) {
            report_semantic_error("A function call cannot be made with non-function type identifier: " + $1->getname());
            $$->set_data_type("error");
        } else {
            $$->set_data_type(func->get_return_type());

            vector<pair<string, string> > params = func->get_parameters();
            vector<string> arg_types;
            string args_str = $3->get_data_type();
            stringstream ss(args_str);
            string item;
            while (getline(ss, item, ',')) {
                if (!item.empty()) arg_types.push_back(item);
            }

            if (arg_types.size() != params.size()) {
                report_semantic_error("Inconsistencies in number of arguments in function call: " + $1->getname());
                $$->set_data_type("error");
            } else {
                bool func_arg_error = false;
                for (size_t i = 0; i < arg_types.size(); ++i) {
                    if (arg_types[i] == "array") {
                        func_arg_error = true;
                    } else if ((params[i].first == "int" || params[i].first == "float") &&
                               (arg_types[i] == "int" || arg_types[i] == "float") &&
                               params[i].first != arg_types[i]) {
                        report_semantic_error("argument " + to_string(i + 1) + " type mismatch in function call: " + $1->getname());
                        func_arg_error = true;
                    }
                }
                if (func_arg_error) {
                    $$->set_data_type("error");
                }
            }
        }
    }
    | LPAREN expression RPAREN
    {
        outlog<<"At line no: "<<lines<<" factor : LPAREN expression RPAREN "<<endl<<endl;
        outlog<<"("<<$2->getname()<<")"<<endl<<endl;

        $$ = new symbol_info("("+$2->getname()+")","fctr");
        $$->set_data_type($2->get_data_type());
    }
    | CONST_INT
    {
        outlog<<"At line no: "<<lines<<" factor : CONST_INT "<<endl<<endl;
        outlog<<$1->getname()<<endl<<endl;

        $$ = new symbol_info($1->getname(),"fctr");
        $$->set_data_type("int");
    }
    | CONST_FLOAT
    {
        outlog<<"At line no: "<<lines<<" factor : CONST_FLOAT "<<endl<<endl;
        outlog<<$1->getname()<<endl<<endl;

        $$ = new symbol_info($1->getname(),"fctr");
        $$->set_data_type("float");
    }
    | variable INCOP
    {
        outlog<<"At line no: "<<lines<<" factor : variable INCOP "<<endl<<endl;
        outlog<<$1->getname()<<"++"<<endl<<endl;

        $$ = new symbol_info($1->getname()+"++","fctr");
        $$->set_data_type($1->get_data_type());
    }
    | variable DECOP
    {
        outlog<<"At line no: "<<lines<<" factor : variable DECOP "<<endl<<endl;
        outlog<<$1->getname()<<"--"<<endl<<endl;

        $$ = new symbol_info($1->getname()+"--","fctr");
        $$->set_data_type($1->get_data_type());
    }
    ;
	
argument_list : arguments
			  {
					outlog<<"At line no: "<<lines<<" argument_list : arguments "<<endl<<endl;
					outlog<<$1->getname()<<endl<<endl;
						
					$$ = new symbol_info($1->getname(),"arg_list");
					$$->set_data_type($1->get_data_type());
			  }
			  |
			  {
					outlog<<"At line no: "<<lines<<" argument_list :  "<<endl<<endl;
					outlog<<""<<endl<<endl;
						
					$$ = new symbol_info("","arg_list");
					$$->set_data_type("");
			  }
			  ;
	
arguments : arguments COMMA logic_expression
          {
                outlog<<"At line no: "<<lines<<" arguments : arguments COMMA logic_expression "<<endl<<endl;
                outlog<<$1->getname()<<","<<$3->getname()<<endl<<endl;

                $$ = new symbol_info($1->getname()+","+$3->getname(),"arg");

                string arg_type = $3->get_data_type();
                string arg_name = $3->getname();
                string base_var_name = arg_name;
                size_t bracket_pos = base_var_name.find('[');
                if (bracket_pos != string::npos) {
                    base_var_name = base_var_name.substr(0, bracket_pos);
                }

                symbol_info* s = lookup_symbol(base_var_name);
                if (s != NULL && arg_name.find('[') == string::npos && s->get_is_array()) {
                    arg_type = "array";
                }

                $$->set_data_type($1->get_data_type() + "," + arg_type);
          }
          | logic_expression
          {
                outlog<<"At line no: "<<lines<<" arguments : logic_expression "<<endl<<endl;
                outlog<<$1->getname()<<endl<<endl;

                $$ = new symbol_info($1->getname(),"arg");

                string arg_type = $1->get_data_type();
                string arg_name = $1->getname();
                string base_var_name = arg_name;
                size_t bracket_pos = base_var_name.find('[');
                if (bracket_pos != string::npos) {
                    base_var_name = base_var_name.substr(0, bracket_pos);
                }

                symbol_info* s = lookup_symbol(base_var_name);
                if (s != NULL && arg_name.find('[') == string::npos && s->get_is_array()) {
                    arg_type = "array";
                }

                $$->set_data_type(arg_type);
          }
          ;
 

%%

int main(int argc, char *argv[])
{
    if(argc != 2)
    {
        cout<<"Please input file name"<<endl;
        return 0;
    }
    yyin = fopen(argv[1], "r");
    outlog.open("21101177_log.txt", ios::trunc);
    errorlog.open("21101177_error.txt", ios::trunc);

    if(yyin == NULL)
    {
        cout<<"Couldn't open file"<<endl;
        return 0;
    }

    table = new symbol_table(10);

    yyparse();

    delete table;

    outlog << endl << endl << "Total lines: " << lines << endl;
    outlog << "Total errors: " << error_count << endl;
    outlog.close();

    errorlog << "Total errors: " << error_count << endl;
    errorlog.close();

    fclose(yyin);

    return 0;
}
