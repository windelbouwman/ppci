all: interop

# Now link all compiled objects (here, just one) into executable. For this,
# we need to provide linker with memory layout file. We'll also use main()
# as the executable entrypoint.
interop: ppci_part.o gcc_part.o
	$(CC) $^ -o $@

gcc_part.o: gcc_part.c
	$(CC) $(CFLAGS) -c $^ -o $@

ppci_part.o: ppci_part.jso
	python -m ppci objcopy --output-format elf $^ $@

ppci_part.jso: ppci_part.c
	python -m ppci cc $(CFLAGS) -c $^ -o $@

clean:
	rm -f *.o hello
