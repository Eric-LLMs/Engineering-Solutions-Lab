#ifndef  __PARSER_H_
#define  __PARSER_H_
#include "build_in.h"
#include "user.h"
#include <stdio.h>
#include <iostream>
#include <string.h>
namespace parse
{   
    class Parser
    {
        static const int MAX_COLUMN = 1024;
    
        const char* column_[MAX_COLUMN];
        int column_num_;
        
        public:
        Parser()
        {
            memset(this, '\0', sizeof(*this));
        }
        
        int parse_line(const char* line, const int column_num) 
        {
            int ret = 0;
            column_num_ = column_num;

            do
            {
                if (NULL == line || column_num <= 0)
                {
                    ret = 1;
                    break;
                }
                int index = 0;
                for (int i = 0; '\n' != line[i]; i++)
                {
                    if (0 == i)
                    {
                        column_[index++] = &line[i];
                        //printf("%s\n", column_[0]);
                    }
                    else if ('\t' == line[i])
                    {
                        column_[index++] = &line[i+1];
                        //printf("%s\n", column_[index-1]);
                    }
                }
                if (column_num != index)
                {
                    ret = 1;
                    break;
                }
            } while(0);
            return ret;
        };
    
        template<class T>
        int get_column(const int index, T* result)
        {
            int ret = 0;
    
            if (index < column_num_)
            {
                ret = parse(column_[index], result);
            }
    
            else
            {
                ret = 1;
            }
    
            return ret;
        }    
    };
}
#endif