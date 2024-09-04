#ifndef  __USER_H_
#define  __USER_H_
#include <stdio.h>
namespace parse
{
    //example
    typedef struct MyStruct
    {
        int a;
        int b;
        int c;
    }MyStruct;
    
    int parse(const char* str, MyStruct* result);
}
#endif