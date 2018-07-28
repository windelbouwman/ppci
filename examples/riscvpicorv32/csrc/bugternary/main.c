#include <stdio.h>
void main_main()
{
    int res;
    res = (1==1) ? 1: (2==2)? 2 : 3;
    if (res != 1) printfdbg("Fail1:%d\n",res);    
}
