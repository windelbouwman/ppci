
hello: barf.o main.c
	gcc -o hello barf.o main.c

barf.o: dynlink.py
	python dynlink.py

clean:
	rm barf.o
	rm hello
