#ifndef SCOPE_TABLE_H
#define SCOPE_TABLE_H

#include "symbol_info.h"

extern ofstream outlog;

class scope_table
{
private:
    int bucket_count;
    int unique_id;
    scope_table *parent_scope;
    vector<list<symbol_info *> > table;

    int hash_function(string name)
    {
        int sum = 0;
        for (char ch : name)
        {
            sum += int(ch);
        }
        return sum % bucket_count;
    }

public:
    scope_table()
    {
        bucket_count = 10;
        unique_id = 1;
        parent_scope = NULL;
        table.resize(bucket_count);
        outlog << "New ScopeTable with ID " << unique_id << " created" << endl << endl;
    }

    scope_table(int bucket_count, int unique_id, scope_table *parent_scope)
    {
        this->bucket_count = bucket_count;
        this->unique_id = unique_id;
        this->parent_scope = parent_scope;
        table.resize(bucket_count);
        outlog << "New ScopeTable with ID " << unique_id << " created" << endl << endl;
    }

    scope_table *get_parent_scope()
    {
        return parent_scope;
    }

    int get_unique_id()
    {
        return unique_id;
    }

    ~scope_table()
    {
        if (unique_id != 1)
        {
            outlog << "Scopetable with ID " << unique_id << " removed" << endl << endl;
        }

        for (auto &bucket : table)
        {
            for (auto symbol : bucket)
            {
                delete symbol;
            }
            bucket.clear();
        }
        table.clear();
    }

    symbol_info *lookup_in_scope(symbol_info *symbol)
    {
        int hash_val = hash_function(symbol->getname());

        for (symbol_info *current : table[hash_val])
        {
            if (current->getname() == symbol->getname())
            {
                return current;
            }
        }
        return NULL;
    }

    bool insert_in_scope(symbol_info *symbol)
    {
        if (lookup_in_scope(symbol) != NULL)
        {
            return false;
        }

        int hash_value = hash_function(symbol->getname());
        table[hash_value].push_back(symbol);
        return true;
    }

    bool delete_from_scope(symbol_info *symbol)
    {
        int hash_val = hash_function(symbol->getname());
        auto &bucket = table[hash_val];

        for (auto it = bucket.begin(); it != bucket.end(); ++it)
        {
            if ((*it)->getname() == symbol->getname())
            {
                bucket.erase(it);
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
            if (!table[i].empty())
            {
                outlog << i << " --> " << endl;
                for (auto current : table[i])
                {
                    outlog << "< " << current->getname() << " : " << current->get_type() << " >" << endl;

                    if (current->get_is_function())
                    {
                        outlog << "Function Definition" << endl;
                        outlog << "Return Type: " << current->get_return_type() << endl;
                        vector<pair<string, string> > params = current->get_parameters();
                        outlog << "Number of Parameters: " << params.size() << endl;
                        outlog << "Parameter Details: ";
                        for (int j = 0; j < (int)params.size(); j++)
                        {
                            outlog << params[j].first << " " << params[j].second;
                            if (j < (int)params.size() - 1)
                            {
                                outlog << ", ";
                            }
                        }
                        outlog << endl;
                    }
                    else if (current->get_is_array())
                    {
                        outlog << "Array" << endl;
                        outlog << "Type: " << current->get_data_type() << endl;
                        outlog << "Size: " << current->get_array_size() << endl;
                    }
                    else
                    {
                        outlog << "Variable" << endl;
                        outlog << "Type: " << current->get_data_type() << endl;
                    }
                }
                outlog << endl;
            }
        }
    }
};

#endif
