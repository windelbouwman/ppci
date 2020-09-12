# One can run this file inside this folder as $make clean && make all

CC = python -m ppci cc --freestanding -I ../../../librt/libc/include
CFLAGS = -O1

all: reading_file

reading_file: reading_file.o
	python -m ppci ld --entry main --layout ../linux64.mmap $^ -o $@

reading_file.o:
	$(CC) reading_file.c ../../../librt/libc/src/*.c ../../../librt/libc/src/*/*.c  -o reading_file.o
	
clean:
	rm -f *.o *.S reading_file.o reading_file