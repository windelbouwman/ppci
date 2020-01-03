CC = python -m ppci cc
CFLAGS = -O1

all: hello

# Now link all compiled objects (here, just one) into executable. For this,
# we need to provide linker with memory layout file. We'll also use main()
# as the executable entrypoint.
hello: hello.o
	python -m ppci ld --entry main --layout linux64.ld $^ -o $@

# We build object files as usual with $(CC) (using the builtin make rule).
hello.o: hello.c

clean:
	rm -f *.o hello
