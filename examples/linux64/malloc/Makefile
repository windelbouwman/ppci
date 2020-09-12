# Here we are compiling our small libc
# You can change the paths to wherever your c files are
# -I flag to specify the headers folder path
# *.c source folders and files must come after the file where main is
# In this case malloc_test.c ...

# One can run this file inside this folder as $make clean && make all

CC = python -m ppci cc --freestanding -I ../../../librt/libc/include
CFLAGS = -O1

all: malloc_test

malloc_test: malloc_test.o
	python -m ppci ld --entry main --layout ../linux64.mmap $^ -o $@

malloc_test.o:
	# in case you want to see the asm, use the -S flag
	# $(CC) malloc_test.c ../../../librt/libc/src/*.c ../../../librt/libc/src/*/*.c -S -o malloc_test.S
	
	$(CC) malloc_test.c ../../../librt/libc/src/*.c ../../../librt/libc/src/*/*.c -o malloc_test.o
	
clean:
	rm -f *.o *.S malloc_test malloc_test.o