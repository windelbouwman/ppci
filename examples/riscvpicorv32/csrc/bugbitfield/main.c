#include <stdarg.h>
#include <mathlib.h>
#include "printf.h"
#include "printf_cfg.h"



void main_main(void) {
 DOUBLE u;
 float f=8.0;
 printf("%x\n",f);
 printf("%f\n",f);
 u.d = f;
  printf("exponent = %x\n", u.D.exponent);
} 