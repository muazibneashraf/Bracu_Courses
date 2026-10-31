#pragma once
#ifndef SCOPE_TABLE_H
#define SCOPE_TABLE_H

#include "symbol_info.h"

class scope_table
{
private:
    int bucket_count;
    int unique_id;
    scope_table *parent_scope;
    vector<list<symbol_info*> > table;

    int hash_function(const string &name) const
    {
        unsigned long long hash_value = 0;
        for (char ch : name)
        {
            hash_value = (hash_value * 31ULL + (unsigned long long)ch) % (unsigned long long)bucket_count;
        }
        return (int)(hash_value % (unsigned long long)bucket_count);
    }

public:
    scope_table() : bucket_count(0), unique_id(0), parent_scope(NULL) {}

    scope_table(int bucket_count, int unique_id, scope_table *parent_scope = NULL)
    {
        this->bucket_count = bucket_count;
        this->unique_id = unique_id;
        this->parent_scope = parent_scope;
        table.resize(bucket_count);
    }

    scope_table *get_parent_scope()
    {
        return parent_scope;
    }

    int get_unique_id()
    {
        return unique_id;
    }

    symbol_info *lookup_in_scope(symbol_info *symbol)
    {
        if (symbol == NULL) return NULL;
        string name = symbol->get_name();
        int index = hash_function(name);
        for (list<symbol_info*>::iterator it = table[index].begin(); it != table[index].end(); ++it)
        {
            if ((*it)->get_name() == name)
            {
                return *it;
            }
        }
        return NULL;
    }

    bool insert_in_scope(symbol_info *symbol)
    {
        if (symbol == NULL) return false;
        if (lookup_in_scope(symbol) != NULL) return false;
        int index = hash_function(symbol->get_name());
        table[index].push_back(symbol);
        return true;
    }

    bool delete_from_scope(symbol_info *symbol)
    {
        if (symbol == NULL) return false;
        string name = symbol->get_name();
        int index = hash_function(name);
        for (list<symbol_info*>::iterator it = table[index].begin(); it != table[index].end(); ++it)
        {
            if ((*it)->get_name() == name)
            {
                delete *it;
                table[index].erase(it);
                return true;
            }
        }
        return false;
    }

    void print_scope_table(ofstream &outlog)
    {
        outlog << "ScopeTable # " << unique_id << endl;
        for (int i = 0; i < bucket_count; i++)
        {
            if (table[i].empty()) continue;
            outlog << i << " --> " << endl;
            for (list<symbol_info*>::iterator it = table[i].begin(); it != table[i].end(); ++it)
            {
                symbol_info *sym = *it;
                outlog << "< " << sym->get_name() << " : " << sym->get_type() << " >" << endl;

                if (sym->get_symbol_type() == "Function")
                {
                    outlog << "Function Definition" << endl;
                    outlog << "Return Type: " << sym->get_data_type() << endl;
                    outlog << "Number of Parameters: " << sym->get_parameter_count() << endl;
                    outlog << "Parameter Details: ";
                    vector<string> details = sym->get_parameter_descriptions();
                    for (size_t j = 0; j < details.size(); j++)
                    {
                        outlog << details[j];
                        if (j + 1 < details.size()) outlog << ", ";
                    }
                    outlog << endl;
                }
                else if (sym->get_symbol_type() == "Array")
                {
                    outlog << "Array" << endl;
                    outlog << "Type: " << sym->get_data_type() << endl;
                    outlog << "Size: " << sym->get_array_size() << endl;
                }
                else
                {
                    outlog << "Variable" << endl;
                    outlog << "Type: " << sym->get_data_type() << endl;
                }
                outlog << endl;
            }
        }
    }

    ~scope_table()
    {
        for (int i = 0; i < bucket_count; i++)
        {
            for (list<symbol_info*>::iterator it = table[i].begin(); it != table[i].end(); ++it)
            {
                delete *it;
            }
            table[i].clear();
        }
    }
};

#endif
