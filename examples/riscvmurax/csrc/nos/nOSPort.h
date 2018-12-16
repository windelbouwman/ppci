/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#ifndef NOSPORT_H
#define NOSPORT_H

#ifdef __cplusplus
extern "C" {
#endif

#define NOS_UNUSED(v)               (void)v

typedef uint32_t                   nOS_Stack;

#define NOS_MEM_ALIGNMENT           __SIZEOF_POINTER__
#define NOS_MEM_POINTER_WIDTH       __SIZEOF_POINTER__
typedef uint32_t                    nOS_StatusReg;

#define NOS_32_BITS_SCHEDULER

#ifdef NOS_CONFIG_ISR_STACK_SIZE
 #if (NOS_CONFIG_ISR_STACK_SIZE == 0)
  #error "nOSConfig.h: NOS_CONFIG_ISR_STACK_SIZE is set to invalid value: must be higher than 0."
 #endif
#endif

 #define MSTATUS_PRV1 0x1880
 
#define nOS_EnterCritical(sr) entercritical()                                                 
#define nOS_LeaveCritical(sr) leavecritical()                                                 
    

nOS_Stack*  nOS_EnterIsr        (nOS_Stack *sp);
nOS_Stack*  nOS_LeaveIsr        (nOS_Stack *sp);


/* Unused function for this port */
#define     nOS_InitSpecific()

#define     nOS_SwitchContext()      nOS_SwitchContextHandler()
void        nOS_SwitchContextHandler    (void);

#ifdef NOS_PRIVATE
 void       nOS_InitContext             (nOS_Thread *thread, nOS_Stack *stack, size_t ssize, nOS_ThreadEntry entry, void *arg);
#endif

#ifdef __cplusplus
}
#endif

#endif /* NOSPORT_H */
