#ifndef SYMBOL_INFO_H
#define SYMBOL_INFO_H

#include <bits/stdc++.h>
using namespace std;

class symbol_info
{
private:
    string name;
    string type;
    symbol_info *next;
    bool is_array;
    int array_size;
    string data_type;
    bool is_function;
    string return_type;
    vector<pair<string, string> > parameters;

public:
    symbol_info()
    {
        name = "";
        type = "";
        next = NULL;
        is_array = false;
        array_size = 0;
        data_type = "";
        is_function = false;
        return_type = "";
    }

    symbol_info(string name, string type)
    {
        this->name = name;
        this->type = type;
        next = NULL;
        is_array = false;
        array_size = 0;
        data_type = "";
        is_function = false;
        return_type = "";
    }

    symbol_info(string name, string type, string data_type)
    {
        this->name = name;
        this->type = type;
        this->data_type = data_type;
        next = NULL;
        is_array = false;
        array_size = 0;
        is_function = false;
        return_type = "";
    }

    symbol_info(string name, string type, string data_type, int array_size)
    {
        this->name = name;
        this->type = type;
        this->data_type = data_type;
        this->array_size = array_size;
        this->is_array = true;
        next = NULL;
        is_function = false;
        return_type = "";
    }

    symbol_info(string name, string type, string return_type, vector<pair<string, string> > params)
    {
        this->name = name;
        this->type = type;
        this->return_type = return_type;
        this->parameters = params;
        this->is_function = true;
        this->data_type = return_type;
        next = NULL;
        is_array = false;
        array_size = 0;
    }

    string getname()
    {
        return name;
    }

    string get_type()
    {
        return type;
    }

    void set_name(string name)
    {
        this->name = name;
    }

    void set_type(string type)
    {
        this->type = type;
    }

    symbol_info *getnext()
    {
        return next;
    }

    string get_data_type()
    {
        return data_type;
    }

    int get_array_size()
    {
        return array_size;
    }

    bool get_is_array()
    {
        return is_array;
    }

    bool get_is_function()
    {
        return is_function;
    }

    string get_return_type()
    {
        return return_type;
    }

    vector<pair<string, string> > get_parameters()
    {
        return parameters;
    }

    void setnext(symbol_info *next)
    {
        this->next = next;
    }

    void set_data_type(string data_type)
    {
        this->data_type = data_type;
    }

    void set_array_size(int size)
    {
        this->array_size = size;
        this->is_array = true;
    }

    void set_as_function(string return_type, vector<pair<string, string> > params)
    {
        this->is_function = true;
        this->return_type = return_type;
        this->parameters = params;
        this->data_type = return_type;
    }

    ~symbol_info()
    {
        next = NULL;
    }
};

#endif
