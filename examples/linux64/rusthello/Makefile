
all: dummy.oj

rusthello.ll: rusthello.rs
	rustc rusthello.rs --emit llvm-ir

dummy.oj: rusthello.ll
	ppci-llc.py -m x86_64 -o dummy.oj rusthello.ll

