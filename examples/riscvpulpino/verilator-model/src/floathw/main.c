#include <stdarg.h>
#include <math.h>
#include "printf.h"
#include "printf_cfg.h"


float a = 0.123;
float b = 0.5;
float c;
int main(void) {
	c = a + b;
	printf("%f + %f=%f\n", a, b, c);
	c = a - b;
	printf("%f - %f=%f\n", a, b, c);
	c = a * b;
	printf("%f * %f=%f\n", a, b, c);
	c = a / b;
	printf("%f / %f=%f\n", a, b, c);
	c = sqrt(b);
	printf("sqrt(%f) =%f\n", b, c);
	while(1){}
} 