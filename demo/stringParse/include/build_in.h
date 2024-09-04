#ifndef  __BUILD_IN_H_
#define  __BUILD_IN_H_
#include <stdint.h>
namespace parse
{
    //int type
    int parse(const char* str, int* result);
    //char* type
    int parse(const char* str, char* result);
    int parse(const char* str, float* result);
    int parse(const char* str, uint32_t* result);
    int parse(const char* str, uint64_t* result);
    void test();
}
#endif