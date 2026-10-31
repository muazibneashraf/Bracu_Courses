#pragma once
#ifndef SYMBOL_TABLE_H
#define SYMBOL_TABLE_H

#include "scope_table.h"

class symbol_table
{
private:
    scope_table *current_scope;
    int bucket_count;
    int next_scope_id;
    ofstream *outlog;

public:
    symbol_table(int bucket_count, ofstream *outlog)
    {
        this->bucket_count = bucket_count;
        this->current_scope = NULL;
        this->next_scope_id = 1;
        this->outlog = outlog;
    }

    ~symbol_table()
    {
        while (current_scope != NULL)
        {
            scope_table *temp = current_scope;
            current_scope = current_scope->get_parent_scope();
            delete temp;
        }
    }

    void enter_scope()
    {
        scope_table *new_scope = new scope_table(bucket_count, next_scope_id++, current_scope);
        current_scope = new_scope;
        if (outlog != NULL)
        {
            (*outlog) << "New ScopeTable with ID " << current_scope->get_unique_id() << " created" << endl << endl;
        }
    }

    void exit_scope()
    {
        if (current_scope == NULL) return;
        if (outlog != NULL)
        {
            (*outlog) << "Scopetable with ID " << current_scope->get_unique_id() << " removed" << endl << endl;
        }
        scope_table *temp = current_scope;
        current_scope = current_scope->get_parent_scope();
        delete temp;
    }

    bool insert(symbol_info *symbol)
    {
        if (current_scope == NULL) return false;
        return current_scope->insert_in_scope(symbol);
    }

    bool remove(symbol_info *symbol)
    {
        if (current_scope == NULL) return false;
        return current_scope->delete_from_scope(symbol);
    }

    symbol_info *lookup(symbol_info *symbol)
    {
        scope_table *temp = current_scope;
        while (temp != NULL)
        {
            symbol_info *result = temp->lookup_in_scope(symbol);
            if (result != NULL) return result;
            temp = temp->get_parent_scope();
        }
        return NULL;
    }

    void print_current_scope(ofstream &out)
    {
        if (current_scope != NULL) current_scope->print_scope_table(out);
    }

    void print_all_scopes(ofstream &out)
    {
        out << "################################" << endl << endl;
        scope_table *temp = current_scope;
        while (temp != NULL)
        {
            temp->print_scope_table(out);
            temp = temp->get_parent_scope();
        }
        out << "################################" << endl << endl;
    }
};

#endif
