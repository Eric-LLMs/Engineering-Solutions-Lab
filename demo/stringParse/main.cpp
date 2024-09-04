#include <iostream>
#include <com_log.h>
#include <stdio.h>
#include "./include/parser.h"
#include <gtest/gtest.h>

using namespace std;
using namespace parse;

int main()
{  
    int ret= com_loadlog("./conf", "comlog.conf");   
    if (ret != 0)
    {
        fprintf(stderr, "load err\n");
        return -1;
    }

    parse::test();
    // testing::InitGoogleTest(&argc, argv);
    // return RUN_ALL_TESTS();
    // char* test1 = "abcdef\t123\t3.9\t456\tyiyg\n";
    // char* test2 = "abcdef\t3:4,5,6\t3.9\t456\tyiyg\t4:1,2,3,4\n";
    // char* test3 = "abcdef\t123\t3.9\t456\tyiyg\t22 33 44\n";
    
    // test.parse_line(test1, 5);
    // int x;
    // test.get_column(3, &x);
    // char* y = new char[20];
    // test.get_column(4, y);
    // float z;
    // test.get_column(2, &z);
    // printf("%d, %s, %f\n", x, y, z);
    // test.parse_line(test3, 6);
    
    // MyStruct my_struct;
    // test.get_column(5, &my_struct);
    // char* res = ("%d %d %d\n", my_struct.a, my_struct.b, my_struct.c)
    // printf(res);
    // com_writelog("URL", res);
    return 0;   
}
