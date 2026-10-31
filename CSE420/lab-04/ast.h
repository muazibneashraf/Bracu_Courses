#ifndef AST_H
#define AST_H

#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

using namespace std;

inline string ast_new_temp(int& temp_count) {
    return "t" + to_string(temp_count++);
}

inline string ast_new_label(int& label_count) {
    return "L" + to_string(label_count++);
}

class ASTNode {
public:
    virtual ~ASTNode() {}
    virtual string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                                 int& temp_count, int& label_count) const = 0;
};

class ExprNode : public ASTNode {
protected:
    string node_type;
public:
    ExprNode(string type) : node_type(type) {}
    virtual string get_type() const { return node_type; }
    virtual ExprNode* clone_expr() const = 0;
};

class VarNode : public ExprNode {
private:
    string name;
    ExprNode* index;

public:
    VarNode(string name, string type, ExprNode* idx = nullptr)
        : ExprNode(type), name(name), index(idx) {}

    ~VarNode() override { delete index; }

    bool has_index() const { return index != nullptr; }
    string get_name() const { return name; }

    string generate_index_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                               int& temp_count, int& label_count) const {
        if (!index) return "";
        return index->generate_code(outcode, symbol_to_temp, temp_count, label_count);
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string temp = ast_new_temp(temp_count);
        if (index) {
            string idx = generate_index_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << temp << " = " << name << "[" << idx << "]" << endl;
        } else {
            outcode << temp << " = " << name << endl;
        }
        symbol_to_temp[name] = temp;
        return temp;
    }

    ExprNode* clone_expr() const override {
        return new VarNode(name, node_type, index ? index->clone_expr() : nullptr);
    }
};

class ConstNode : public ExprNode {
private:
    string value;

public:
    ConstNode(string val, string type) : ExprNode(type), value(val) {}

    string generate_code(ofstream& outcode, map<string, string>&,
                         int& temp_count, int&) const override {
        string temp = ast_new_temp(temp_count);
        outcode << temp << " = " << value << endl;
        return temp;
    }

    ExprNode* clone_expr() const override {
        return new ConstNode(value, node_type);
    }
};

class BinaryOpNode : public ExprNode {
private:
    string op;
    ExprNode* left;
    ExprNode* right;

public:
    BinaryOpNode(string op, ExprNode* left, ExprNode* right, string result_type)
        : ExprNode(result_type), op(op), left(left), right(right) {}

    ~BinaryOpNode() override {
        delete left;
        delete right;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string lhs = left->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        string rhs = right->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        string temp = ast_new_temp(temp_count);
        outcode << temp << " = " << lhs << " " << op << " " << rhs << endl;
        return temp;
    }

    ExprNode* clone_expr() const override {
        return new BinaryOpNode(op, left ? left->clone_expr() : nullptr,
                                right ? right->clone_expr() : nullptr, node_type);
    }
};

class UnaryOpNode : public ExprNode {
private:
    string op;
    ExprNode* expr;

public:
    UnaryOpNode(string op, ExprNode* expr, string result_type)
        : ExprNode(result_type), op(op), expr(expr) {}

    ~UnaryOpNode() override { delete expr; }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string operand = expr->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        if (op == "+") return operand;
        string temp = ast_new_temp(temp_count);
        outcode << temp << " = " << op << operand << endl;
        return temp;
    }

    ExprNode* clone_expr() const override {
        return new UnaryOpNode(op, expr ? expr->clone_expr() : nullptr, node_type);
    }
};

class AssignNode : public ExprNode {
private:
    VarNode* lhs;
    ExprNode* rhs;

public:
    AssignNode(VarNode* lhs, ExprNode* rhs, string result_type)
        : ExprNode(result_type), lhs(lhs), rhs(rhs) {}

    ~AssignNode() override {
        delete lhs;
        delete rhs;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string rhs_temp = rhs->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        if (lhs->has_index()) {
            string idx = lhs->generate_index_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << lhs->get_name() << "[" << idx << "] = " << rhs_temp << endl;
        } else {
            outcode << lhs->get_name() << " = " << rhs_temp << endl;
            symbol_to_temp[lhs->get_name()] = rhs_temp;
        }
        return rhs_temp;
    }

    ExprNode* clone_expr() const override {
        return new AssignNode(dynamic_cast<VarNode*>(lhs ? lhs->clone_expr() : nullptr),
                              rhs ? rhs->clone_expr() : nullptr, node_type);
    }
};

class StmtNode : public ASTNode {
public:
    virtual string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                                 int& temp_count, int& label_count) const = 0;
};

class ExprStmtNode : public StmtNode {
private:
    ExprNode* expr;

public:
    ExprStmtNode(ExprNode* e) : expr(e) {}
    ~ExprStmtNode() override { delete expr; }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        if (expr) return expr->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        return "";
    }
};

class BlockNode : public StmtNode {
private:
    vector<StmtNode*> statements;

public:
    ~BlockNode() override {
        for (auto stmt : statements) delete stmt;
    }

    void add_statement(StmtNode* stmt) {
        if (stmt) statements.push_back(stmt);
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string last;
        for (auto stmt : statements) {
            if (stmt) last = stmt->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        }
        return last;
    }
};

class IfNode : public StmtNode {
private:
    ExprNode* condition;
    StmtNode* then_block;
    StmtNode* else_block;

public:
    IfNode(ExprNode* cond, StmtNode* then_stmt, StmtNode* else_stmt = nullptr)
        : condition(cond), then_block(then_stmt), else_block(else_stmt) {}

    ~IfNode() override {
        delete condition;
        delete then_block;
        delete else_block;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string cond = condition->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        if (else_block) {
            string true_label = ast_new_label(label_count);
            string false_label = ast_new_label(label_count);
            string end_label = ast_new_label(label_count);
            outcode << "if " << cond << " goto " << true_label << endl;
            outcode << "goto " << false_label << endl;
            outcode << true_label << ":" << endl;
            then_block->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << "goto " << end_label << endl;
            outcode << false_label << ":" << endl;
            else_block->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << end_label << ":" << endl;
        } else {
            string true_label = ast_new_label(label_count);
            string end_label = ast_new_label(label_count);
            outcode << "if " << cond << " goto " << true_label << endl;
            outcode << "goto " << end_label << endl;
            outcode << true_label << ":" << endl;
            then_block->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << end_label << ":" << endl;
        }
        return "";
    }
};

class WhileNode : public StmtNode {
private:
    ExprNode* condition;
    StmtNode* body;

public:
    WhileNode(ExprNode* cond, StmtNode* body_stmt)
        : condition(cond), body(body_stmt) {}

    ~WhileNode() override {
        delete condition;
        delete body;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        string start_label = ast_new_label(label_count);
        string body_label = ast_new_label(label_count);
        string end_label = ast_new_label(label_count);
        outcode << start_label << ":" << endl;
        string cond = condition->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        outcode << "if " << cond << " goto " << body_label << endl;
        outcode << "goto " << end_label << endl;
        outcode << body_label << ":" << endl;
        body->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        outcode << "goto " << start_label << endl;
        outcode << end_label << ":" << endl;
        return "";
    }
};

class ForNode : public StmtNode {
private:
    ExprNode* init;
    ExprNode* condition;
    ExprNode* update;
    StmtNode* body;

public:
    ForNode(ExprNode* init_expr, ExprNode* cond_expr, ExprNode* update_expr, StmtNode* body_stmt)
        : init(init_expr), condition(cond_expr), update(update_expr), body(body_stmt) {}

    ~ForNode() override {
        delete init;
        delete condition;
        delete update;
        delete body;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        if (init) init->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        string start_label = ast_new_label(label_count);
        string body_label = ast_new_label(label_count);
        string end_label = ast_new_label(label_count);
        outcode << start_label << ":" << endl;
        if (condition) {
            string cond = condition->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << "if " << cond << " goto " << body_label << endl;
            outcode << "goto " << end_label << endl;
        } else {
            outcode << "goto " << body_label << endl;
        }
        outcode << body_label << ":" << endl;
        body->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        if (update) update->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        outcode << "goto " << start_label << endl;
        outcode << end_label << ":" << endl;
        return "";
    }
};

class ReturnNode : public StmtNode {
private:
    ExprNode* expr;

public:
    ReturnNode(ExprNode* e) : expr(e) {}
    ~ReturnNode() override { delete expr; }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        if (expr) {
            string value = expr->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << "return " << value << endl;
            return value;
        }
        outcode << "return" << endl;
        return "";
    }
};

class DeclNode : public StmtNode {
private:
    string type;
    vector<pair<string, int>> vars;

public:
    DeclNode(string t) : type(t) {}

    void add_var(string name, int array_size = 0) {
        vars.push_back(make_pair(name, array_size));
    }

    string generate_code(ofstream& outcode, map<string, string>&,
                         int&, int&) const override {
        for (const auto& var : vars) {
            if (var.second > 0) outcode << "// Declaration: " << type << " " << var.first << "[" << var.second << "]" << endl;
            else outcode << "// Declaration: " << type << " " << var.first << endl;
        }
        return "";
    }

    string get_type() const { return type; }
    const vector<pair<string, int>>& get_vars() const { return vars; }
};

class FuncDeclNode : public ASTNode {
private:
    string return_type;
    string name;
    vector<pair<string, string>> params;
    BlockNode* body;

public:
    FuncDeclNode(string ret_type, string n) : return_type(ret_type), name(n), body(nullptr) {}
    ~FuncDeclNode() override { delete body; }

    void add_param(string type, string param_name) {
        params.push_back(make_pair(type, param_name));
    }

    void set_body(BlockNode* b) {
        body = b;
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        outcode << "// Function: " << return_type << " " << name << "(";
        for (size_t i = 0; i < params.size(); ++i) {
            if (i) outcode << ", ";
            outcode << params[i].first << " " << params[i].second;
        }
        outcode << ")" << endl;
        if (body) body->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        outcode << endl;
        return "";
    }
};

class ArgumentsNode : public ASTNode {
private:
    vector<ExprNode*> args;

public:
    ~ArgumentsNode() override { for (auto arg : args) delete arg; }

    void add_argument(ExprNode* arg) {
        if (arg) args.push_back(arg);
    }

    ExprNode* get_argument(int index) const {
        if (index >= 0 && static_cast<size_t>(index) < args.size()) return args[index];
        return nullptr;
    }

    size_t size() const { return args.size(); }
    const vector<ExprNode*>& get_arguments() const { return args; }

    string generate_code(ofstream&, map<string, string>&,
                         int&, int&) const override {
        return "";
    }
};

class FuncCallNode : public ExprNode {
private:
    string func_name;
    vector<ExprNode*> arguments;

public:
    FuncCallNode(string name, string result_type)
        : ExprNode(result_type), func_name(name) {}

    ~FuncCallNode() override {
        for (auto arg : arguments) delete arg;
    }

    void add_argument(ExprNode* arg) {
        if (arg) arguments.push_back(arg);
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        for (auto arg : arguments) {
            string value = arg->generate_code(outcode, symbol_to_temp, temp_count, label_count);
            outcode << "param " << value << endl;
        }
        if (node_type == "void") {
            outcode << "call " << func_name << ", " << arguments.size() << endl;
            return "";
        }
        string temp = ast_new_temp(temp_count);
        outcode << temp << " = call " << func_name << ", " << arguments.size() << endl;
        return temp;
    }

    ExprNode* clone_expr() const override {
        FuncCallNode* cloned = new FuncCallNode(func_name, node_type);
        for (auto arg : arguments) cloned->add_argument(arg ? arg->clone_expr() : nullptr);
        return cloned;
    }
};

class ProgramNode : public ASTNode {
private:
    vector<ASTNode*> units;

public:
    ~ProgramNode() override {
        for (auto unit : units) delete unit;
    }

    void add_unit(ASTNode* unit) {
        if (unit) units.push_back(unit);
    }

    string generate_code(ofstream& outcode, map<string, string>& symbol_to_temp,
                         int& temp_count, int& label_count) const override {
        for (auto unit : units) {
            if (unit) unit->generate_code(outcode, symbol_to_temp, temp_count, label_count);
        }
        return "";
    }
};

#endif // AST_H
