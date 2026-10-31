#pragma once
#ifndef SYMBOL_INFO_H
#define SYMBOL_INFO_H

#include <bits/stdc++.h>
using namespace std;

class symbol_info
{
private:
    string name;
    string type;
    string symbol_type;
    string data_type;
    int array_size;
    vector<string> parameter_types;
    vector<string> parameter_names;

public:
    symbol_info() : name(""), type(""), symbol_type(""), data_type(""), array_size(-1) {}

    symbol_info(string name, string type)
    {
        this->name = name;
        this->type = type;
        this->symbol_type = "";
        this->data_type = "";
        this->array_size = -1;
    }

    string get_name() const { return name; }
    string get_type() const { return type; }
    string get_symbol_type() const { return symbol_type; }
    string get_data_type() const { return data_type; }
    int get_array_size() const { return array_size; }
    const vector<string>& get_parameter_types() const { return parameter_types; }
    const vector<string>& get_parameter_names() const { return parameter_names; }

    void set_name(const string &value) { name = value; }
    void set_type(const string &value) { type = value; }
    void set_symbol_type(const string &value) { symbol_type = value; }
    void set_data_type(const string &value) { data_type = value; }
    void set_array_size(int value) { array_size = value; }

    void add_parameter(const string &param_type, const string &param_name = "")
    {
        parameter_types.push_back(param_type);
        parameter_names.push_back(param_name);
    }

    void copy_parameters_from(const symbol_info *other)
    {
        if (other == NULL) return;
        for (size_t i = 0; i < other->parameter_types.size(); i++)
        {
            parameter_types.push_back(other->parameter_types[i]);
            parameter_names.push_back(other->parameter_names[i]);
        }
    }

    int get_parameter_count() const
    {
        return (int)parameter_types.size();
    }

    vector<string> get_parameter_descriptions() const
    {
        vector<string> result;
        for (size_t i = 0; i < parameter_types.size(); i++)
        {
            if (parameter_names[i].empty()) result.push_back(parameter_types[i]);
            else result.push_back(parameter_types[i] + " " + parameter_names[i]);
        }
        return result;
    }

    ~symbol_info() {}
};

#endif
