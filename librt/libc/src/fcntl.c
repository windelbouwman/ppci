#include "stdlib.h"
#include "fcntl.h"

int open(const char *filename, int mode){
	return syscall(2, filename, mode, 0);
}