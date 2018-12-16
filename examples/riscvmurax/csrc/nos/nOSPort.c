/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#define NOS_PRIVATE
#include "nOS.h"

#ifdef __cplusplus
extern "C" {
#endif

#ifdef NOS_CONFIG_ISR_STACK_SIZE
 static nOS_Stack _isrStack[NOS_CONFIG_ISR_STACK_SIZE];
#endif

#define REGSAVESIZE 32*4
void nOS_InitContext(nOS_Thread *thread, nOS_Stack *stack, size_t ssize, nOS_ThreadEntry entry, void *arg)
{
    /* Stack grow from high to low address */
    nOS_Stack   *tos    = (nOS_Stack*)((uint32_t)stack + ssize - 4 - REGSAVESIZE);
    thread->stackPtr = tos;
    tos[31] = (nOS_Stack)entry;
    tos[11] = (nOS_Stack)arg;
}


nOS_Stack* nOS_EnterIsr (nOS_Stack *sp)
{
#if (NOS_CONFIG_SAFE > 0)
    if (nOS_running)
#endif
    {
        if (nOS_isrNestingCounter == 0) {
            nOS_runningThread->stackPtr = sp;
#ifdef NOS_CONFIG_ISR_STACK_SIZE
            sp = &_isrStack[NOS_CONFIG_ISR_STACK_SIZE-1];
#else
            sp = nOS_idleHandle.stackPtr;
#endif
        }
        nOS_isrNestingCounter++;
    }

    return sp;
}

nOS_Stack* nOS_LeaveIsr (nOS_Stack *sp)
{
#if (NOS_CONFIG_SAFE > 0)
    if (nOS_running)
#endif
    {
        nOS_isrNestingCounter--;
        if (nOS_isrNestingCounter == 0) {
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0) || (NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE > 0)
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
            if (nOS_lockNestingCounter == 0)
 #endif
            {
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO == 0)
                nOS_highPrioThread = nOS_GetHeadOfList(&nOS_readyThreadsList);
 #elif (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                nOS_highPrioThread = nOS_FindHighPrioThread();
 #else
                nOS_highPrioThread = nOS_GetHeadOfList(&nOS_readyThreadsList[nOS_runningThread->prio]);
 #endif
                nOS_runningThread = nOS_highPrioThread;
            }
#endif
            sp = nOS_runningThread->stackPtr;
        }
    }

    return sp;
}

#ifdef __cplusplus
}
#endif
