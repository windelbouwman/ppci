#include "stdlib.h"
#include "sys/stat.h"

void fstat(int fd, void * statstruct){
    syscall(5, fd, (long) statstruct, 0);
}

inline int f_size(int fd){
	// needs to inform the size of kernel linux stat struct size
	// which is 144 bytes in x86_64 systems
    char buffer[144];

    void * statstruct = (void*)(&buffer);

    fstat(fd, statstruct);
    
    // from the begin to the size part, we have 
	// 8 + 8 + 8 + 8 + 4 + 4 + 8 = 48 bytes
	long size = *((long*)(statstruct + 48));

    return size;
}