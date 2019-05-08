.align  4 
enable_interrupts:
    sw x15, -4(x2)
    li x15, 0x80
    csrs mie, x15
    li x15, 0x1888
    csrs mstatus, x15
    lw x15, -4(x2)
    jalr x0, x1, 0 


.align  4 
entercritical:
    csrci mstatus, 8
    jalr x0, x1, 0 
    

.align  4 
leavecritical:
    csrsi mstatus, 8
    jalr x0, x1, 0 
    

.align  4 
nOS_SwitchContextHandler:
        ;/* Push all registers to running thread stack */
        addi x2, x2, -128
        sw         x1,  124(x2)
        
        sw         x1,  0(x2)
        sw         x4, 12(x2)
        sw         x5, 16(x2)
        sw         x6, 20(x2)
        sw         x7, 24(x2)
        sw         x8, 28(x2)
        sw         x9, 32(x2)
        sw         x10,36(x2)
        sw         x11,40(x2)
        sw         x12,44(x2)
        sw         x13,48(x2)
        sw         x14,52(x2)
        sw         x15,56(x2)
        sw         x16,60(x2)
        sw         x17,64(x2)
        sw         x18,68(x2)
        sw         x19,72(x2)
        sw         x20,76(x2)
        sw         x21,80(x2)
        sw         x22,84(x2)
        sw         x23,88(x2)
        sw         x24,92(x2)
        sw         x25,96(x2)
        sw         x26,100(x2)
        sw         x27,104(x2)
        sw         x28,108(x2)
        sw         x29,112(x2)
        sw         x30,116(x2)
        sw         x31,120(x2)
       
        
        ;/* Save stack pointer to running thread structure */
        lw     x12, nOS_runningThread
        sw     x2, 0(x12)
        ;/* Copy nOS_highPrioThread to nOS_runningThread */
        lw      x12, nOS_highPrioThread
        la      x11, nOS_runningThread
        sw      x12, 0(x11)
        ;/* Restore stack pointer from high prio thread structure */
        lw      x2, 0(x12)
        ;/* Pop all registers from high prio thread stack */
        li         x5, 0x1880
        csrs       mstatus, x5
        lw         x5, 124(x2)
        csrw       mepc, x5
        lw         x1,  0(x2)
        lw         x4, 12(x2)
        lw         x5, 16(x2)
        lw         x6, 20(x2)
        lw         x7, 24(x2)
        lw         x8, 28(x2)
        lw         x9, 32(x2)
        lw         x10,36(x2)
        lw         x11,40(x2)
        lw         x12,44(x2)
        lw         x13,48(x2)
        lw         x14,52(x2)
        lw         x15,56(x2)
        lw         x16,60(x2)
        lw         x17,64(x2)
        lw         x18,68(x2)
        lw         x19,72(x2)
        lw         x20,76(x2)
        lw         x21,80(x2)
        lw         x22,84(x2)
        lw         x23,88(x2)
        lw         x24,92(x2)
        lw         x25,96(x2)
        lw         x26,100(x2)
        lw         x27,104(x2)
        lw         x28,108(x2)
        lw         x29,112(x2)
        lw         x30,116(x2)
        lw         x31,120(x2)
        addi x2, x2, 128
        mret
        

.align  4 
TIMER_CMP_ISR:
        
        addi x2, x2, -128
        csrr       x5, mepc
        sw         x5,  124(x2)
        
        sw         x1,  0(x2)
        sw         x4, 12(x2)
        sw         x5, 16(x2)
        sw         x6, 20(x2)
        sw         x7, 24(x2)
        sw         x8, 28(x2)
        sw         x9, 32(x2)
        sw         x10,36(x2)
        sw         x11,40(x2)
        sw         x12,44(x2)
        sw         x13,48(x2)
        sw         x14,52(x2)
        sw         x15,56(x2)
        sw         x16,60(x2)
        sw         x17,64(x2)
        sw         x18,68(x2)
        sw         x19,72(x2)
        sw         x20,76(x2)
        sw         x21,80(x2)
        sw         x22,84(x2)
        sw         x23,88(x2)
        sw         x24,92(x2)
        sw         x25,96(x2)
        sw         x26,100(x2)
        sw         x27,104(x2)
        sw         x28,108(x2)
        sw         x29,112(x2)
        sw         x30,116(x2)
        sw         x31,120(x2)
        
        ;/* Switch to isr stack if isr nesting counter is zero */                \
        mv         x12,x2
        jal        x1, nOS_EnterIsr
        mv         x2, x10
        
        jal        x1, Isr
        
        ;/* Switch to high prio thread stack if isr nesting counter reach zero */\
        mv         x12, x2
        jal         x1, nOS_LeaveIsr
        ;/* Pop all registers from high prio thread stack */                     \
        mv         x2, x10
        li         x5, 0x1880
        csrw       mstatus, x5
        lw         x5, 124(x2)
        csrw       mepc, x5
        lw         x1,  0(x2)
        lw         x4, 12(x2)
        lw         x5, 16(x2)
        lw         x6, 20(x2)
        lw         x7, 24(x2)
        lw         x8, 28(x2)
        lw         x9, 32(x2)
        lw         x10,36(x2)
        lw         x11,40(x2)
        lw         x12,44(x2)
        lw         x13,48(x2)
        lw         x14,52(x2)
        lw         x15,56(x2)
        lw         x16,60(x2)
        lw         x17,64(x2)
        lw         x18,68(x2)
        lw         x19,72(x2)
        lw         x20,76(x2)
        lw         x21,80(x2)
        lw         x22,84(x2)
        lw         x23,88(x2)
        lw         x24,92(x2)
        lw         x25,96(x2)
        lw         x26,100(x2)
        lw         x27,104(x2)
        lw         x28,108(x2)
        lw         x29,112(x2)
        lw         x30,116(x2)
        lw         x31,120(x2)
        addi x2, x2, 128
        mret
    

