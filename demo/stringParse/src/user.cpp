#include "../include/user.h"
namespace parse
{
    //对于用户类型，请自定义解析实现
    int parse(const char* str, MyStruct* result)
    {
        sscanf(str, "%d %d %d", &result->a, &result->b, &result->c);
    
        return 0;
    } 
}