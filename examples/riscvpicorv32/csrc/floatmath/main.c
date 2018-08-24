#include <stdarg.h>
#include <math.h>
#include <mathlib.h>
#include "printf.h"
#include "printf_cfg.h"



void main_main(void) {
  printf("cos(Pi/4) = %f\n", cos(PI/4));
  printf("sin(Pi/4) = %f\n", sin(PI/4));
  printf("exp(Pi/4) = %f\n", exp(PI/4));
  printf("ln(Pi/4) = %f\n", log(PI/4));
  printf("sqrt(Pi/4) = %f\n", sqrt(PI/4));
} 