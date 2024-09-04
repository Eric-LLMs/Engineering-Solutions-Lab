#include <stdio.h>
#include <stdint.h>
#include "../include/build_in.h"
namespace parse
{
    //int type
    int parse(const char* str, int* result)
    {
        int ret = 0;
    
        if (NULL != str)
        {
            if (1 != sscanf(str, "%d", result))
            {
                ret = 1; 
            }
        }
    
        else
        {
            ret = 1;
        }
    
        return ret;
    }
    
    //char* type
    int parse(const char* str, char* result)
    {
        int ret = 0;
    
        if (NULL != str && NULL != result)
        {
            const char* start_str = str;
            char* result_str = result;
    
            while ('\t' != *start_str 
                    && '\n' != *start_str 
                    && '\0' != *start_str
                    && ',' != *start_str)
            {
                *result_str++ = *start_str++;
            }
    
            *result_str = '\0';
        }
    
        else
        {
            ret = 1;
        }
    
        return ret; 
    }

    //flat type
    int parse(const char* str, float* result)
    {
        int ret = 0;
    
        if (NULL != str)
        {
            if (1 != sscanf(str, "%f", result))
            {
                ret = 1; 
            }
        }
    
        else
        {
            ret = 1;
        }
    
        return ret;
    }
}