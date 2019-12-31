  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  nop
  
  nop
  nop
  nop
  
  jal x0, default_exc_handler
  ; reset vector 
  jal x0, reset_handler
  ; illegal instruction exception  
  jal x0, default_exc_handler
  ; ecall handler
  jal x0, default_exc_handler
  
default_exc_handler:
  jal x0, default_exc_handler

reset_handler:
  ;/* set all registers to zero */
  mv  x1, x0
  mv  x2, x1
  mv  x3, x1
  mv  x4, x1
  mv  x5, x1
  mv  x6, x1
  mv  x7, x1
  mv  x8, x1
  mv  x9, x1
  mv x10, x1
  mv x11, x1
  mv x12, x1
  mv x13, x1
  mv x14, x1
  mv x15, x1
  mv x16, x1
  mv x17, x1
  mv x18, x1
  mv x19, x1
  mv x20, x1
  mv x21, x1
  mv x22, x1
  mv x23, x1
  mv x24, x1
  mv x25, x1
  mv x26, x1
  mv x27, x1
  mv x28, x1
  mv x29, x1
  mv x30, x1
  mv x31, x1

  ;/* stack initilization */
  lui x2, 0x1F  

main_entry:
  ;/* jump to main program entry point (argc = argv = 0) */  
  addi x10, x0, 0
  addi x11, x0, 0
  global main
  jal x1, main
  ebreak
