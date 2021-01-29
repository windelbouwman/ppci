#include "stdlib.h"
#include "unistd.h"

ssize_t read(int fd, void *buf, size_t count){
	return (size_t) syscall(0, fd, buf, count);
}

int close(int fd){
    return syscall(3, fd, 0, 0);
}
