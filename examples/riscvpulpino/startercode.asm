repeat 29
nop
endrepeat
jal x0, int_handler
nop
jal x0, int_handler
jal x0, reset_handler
jal x0, illegal_handler
jal x0, illegal_handler
illegal_handler:	
int_handler:
jal x0, int_handler
reset_handler:
lui sp, 0x108000 			
jal ra, main_main
sbreak
