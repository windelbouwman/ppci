#include <stdlib.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h> 

// In this example we will be using some low level functions to open, read and close a file from the system

int main(int argc, char **argv){
    // The function open and the flag O_RDONLY are defined in fcntl.h
    // It is a thin wrapper around a bare syscall
    int fd = open("example.txt",O_RDONLY);

    if (fd == -1){
		printf("ERROR: Could not open the file");
		exit(1);
	}

    // f_size is a helper function defined in sys/stat.h for this libc
    // It is a wrapper around the fstat syscall to get the size in bytes of the file
    long buffer_size = f_size(fd);

    if (buffer_size == -1){
		printf("Error while getting the file size");
		exit(1);
	}

    // Malloc also uses syscalls to get memory from the system
    void *buffer = malloc(buffer_size);

    // Both read and close are defined in unistd.h
    // Both are wrappers around bare syscalls
    ssize_t size = read(fd, buffer, (size_t)buffer_size);

    if (size == -1){
		printf("Error while reading file to buffer");
		exit(1);
	}

    if (close(fd) == -1){
        printf("Error while closing the file");
		exit(1);
    }

    printf("%s",(char*)buffer);

    exit(0);
}