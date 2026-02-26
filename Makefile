COMPILER=atalla_cc
ARCH=atalla
PPCI=python3 -m ppci
INPUT=examples/c/sample2.c

# SRC1=instructtest2.c
SRC1=instructtest3.c
# SRC1=instructtest4.c
SRC2=helper.c

# OBJ1=instructtest2.o
OBJ1=instructtest3.o
# OBJ1=instructtest4.o
OBJ2=helper.o

# OBJ3=instructtest2.s
OBJ3=instructtest3.s
# OBJ3=instructtest4.s
OBJ4=helper.s

ELF=output.elf


# -------------------------
# Single-file compile (old)
# -------------------------
atalla-compile-o2-no-link:
	${PPCI} ${COMPILER} $(SRC1) -m ${ARCH} -O2 --super-verbose


# -------------------------
# Compile BOTH files to .o
# -------------------------
atalla-compile-objects:
	${PPCI} ${COMPILER} $(SRC1) -m ${ARCH} -O2 -c -o $(OBJ1)
	${PPCI} ${COMPILER} $(SRC2) -m ${ARCH} -O2 -c -o $(OBJ2)

# ------------------------------------------------------------
# Generates Assembly Files for Comparison for the disassembler
# ------------------------------------------------------------
atalla-gen-asmfiles:
	${PPCI} ${COMPILER} $(SRC1) -m ${ARCH} -O2 -S -o $(OBJ3)
	${PPCI} ${COMPILER} $(SRC2) -m ${ARCH} -O2 -S -o $(OBJ4)

# -----------------------------
# Link them (FORCES relocation)
# -----------------------------
atalla-link:
	${PPCI} ld $(OBJ1) $(OBJ2) -o $(ELF)

# -------------------------
# One command: build + link
# -------------------------
atalla-test-link: atalla-compile-objects atalla-link
	@echo "Relocation test build complete."

# ------------------------------------------
# Dump the elf file and run the disassembler
# ------------------------------------------
atalla-dump-dis:
	python3 dump_elf.py
	python3 disassemble.py
	@echo "Dumping binary elf file and disassembly complete!"

#----------------------------------
# ONE COMMAND TO RULE THEM ALL!!!!!
#----------------------------------
atalla-run-all: atalla-gen-asmfiles atalla-test-link atalla-dump-dis

#--------------------------
# Test relocations
#--------------------------
atalla-test-reloc:
	python3 test_relocations.py

# -------------------------
# Clean
# -------------------------
clean:
	rm -f *.o *.elf *.s f.txt disassembly.txt output_detailed.txt

