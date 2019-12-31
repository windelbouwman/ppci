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

#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
static void _SuspendThread (void *payload, void *arg)
{
    nOS_Thread *thread = (nOS_Thread*)payload;

    /* Avoid warning */
    NOS_UNUSED(arg);

    /* If thread not already suspended */
    if ( !(thread->state & NOS_THREAD_SUSPENDED) ) {
        if (thread->state == NOS_THREAD_READY) {
            nOS_RemoveThreadFromReadyList(thread);
        }
        thread->state = (nOS_ThreadState)(thread->state | NOS_THREAD_SUSPENDED);
    }
}

static void _ResumeThread (void *payload, void *arg)
{
    nOS_Thread  *thread = (nOS_Thread*)payload;

    NOS_UNUSED(arg);

    if (thread->state & NOS_THREAD_SUSPENDED) {
        thread->state = (nOS_ThreadState)(thread->state &~ NOS_THREAD_SUSPENDED);
        if (thread->state == NOS_THREAD_READY) {
            nOS_AppendThreadToReadyList(thread);
        }
    }
}
#endif  /* NOS_CONFIG_THREAD_SUSPEND_ENABLE */

#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
void nOS_TickThread (void *payload, void *arg)
{
    nOS_Thread      *thread = (nOS_Thread*)payload;
    nOS_ThreadState state   = (nOS_ThreadState)(thread->state & NOS_THREAD_WAITING_MASK);
    nOS_TickCounter ticks   = *(nOS_TickCounter *)arg;
    nOS_Error       err;

    if ((thread->timeout - nOS_tickCounter) <= ticks) {
        err = NOS_E_TIMEOUT;
#if (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
        if (state == NOS_THREAD_SLEEPING) {
            err = NOS_OK;
        }
#endif
        nOS_WakeUpThread(thread, err);
    }
}
#endif  /* NOS_CONFIG_WAITING_TIMEOUT_ENABLE & NOS_CONFIG_SLEEP_ENABLE & NOS_CONFIG_SLEEP_UNTIL_ENABLE */

void nOS_WakeUpThread (nOS_Thread *thread, nOS_Error err)
{
    if (thread->event != NULL) {
        nOS_RemoveFromList(&thread->event->waitList, &thread->readyWait);
    }
    thread->error = (int)err;
    thread->state = (nOS_ThreadState)(thread->state &~ NOS_THREAD_WAITING_MASK);
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
    if (thread->state & NOS_THREAD_WAIT_TIMEOUT) {
        thread->state = (nOS_ThreadState)(thread->state &~ NOS_THREAD_WAIT_TIMEOUT);
        nOS_RemoveFromList(&nOS_timeoutThreadsList, &thread->tout);
    }
#endif
    if (thread->state == NOS_THREAD_READY) {
        nOS_AppendThreadToReadyList(thread);
    }
}

#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
int nOS_ThreadWrapper (void *arg)
{
    nOS_StatusReg   sr;
    nOS_ThreadEntry entry = (nOS_ThreadEntry)nOS_runningThread->ext;
    int             ret;
    nOS_Thread      *thread;

    ret = entry(arg);

    nOS_EnterCritical(sr);
    nOS_runningThread->error = ret;
    nOS_runningThread->state = NOS_THREAD_FINISHED;
    do {
        thread = nOS_SendEvent((nOS_Event*)&nOS_runningThread->joined, NOS_OK);
        if (thread != NULL) {
            if (thread->ext != NULL) {
                *(int*)thread->ext = ret;
            }
        }
    } while (thread != NULL);
    nOS_RemoveThreadFromReadyList(nOS_runningThread);
    nOS_LeaveCritical(sr);

    nOS_Schedule();

    /* will never go here */
    return 0;
}
#endif

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
 #if (NOS_CONFIG_THREAD_SET_PRIO_ENABLE > 0) || (NOS_CONFIG_MUTEX_ENABLE > 0)
void nOS_SetThreadPrio (nOS_Thread *thread, uint8_t prio)
{
    if (thread->prio != prio)
    {
        if (thread->state == NOS_THREAD_READY)
        {
            nOS_RemoveThreadFromReadyList(thread);
        }
        thread->prio = prio;
        if (thread->state == NOS_THREAD_READY)
        {
            nOS_AppendThreadToReadyList(thread);
        }
    }
}
 #endif /* NOS_CONFIG_THREAD_SET_PRIO_ENABLE || NOS_CONFIG_MUTEX_ENABLE */
#endif  /* NOS_CONFIG_HIGHEST_THREAD_PRIO */

nOS_Error nOS_ThreadCreate (nOS_Thread *thread,
                            nOS_ThreadEntry entry,
                            void *arg,
                            nOS_Stack *stack,
                            size_t ssize
#ifdef NOS_USE_SEPARATE_CALL_STACK
                           ,size_t cssize
#endif
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                           ,uint8_t prio
#endif
#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
                           ,nOS_ThreadState state
#endif
#if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
                           ,const char *name
#endif
                           )
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (thread == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (thread == &nOS_idleHandle) {
        err = NOS_E_INV_OBJ;
    }
    else if (entry == NULL) {
        err = NOS_E_INV_VAL;
    }
    else if (stack == NULL) {
        err = NOS_E_INV_VAL;
    } else
 #ifndef NOS_SIMULATED_STACK
    if (ssize == 0) {
        err = NOS_E_INV_VAL;
    } else
 #endif
 #ifdef NOS_USE_SEPARATE_CALL_STACK
    if (cssize == 0) {
        err = NOS_E_INV_VAL;
    } else
 #endif
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
    if (prio > NOS_CONFIG_HIGHEST_THREAD_PRIO) {
        err = NOS_E_INV_PRIO;
    } else
 #endif
 #if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
    if ((state != NOS_THREAD_READY) && (state != NOS_THREAD_SUSPENDED)) {
        err = NOS_E_INV_STATE;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state != NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
            thread->prio = prio;
#endif
            thread->state = NOS_THREAD_READY;
#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
            if (state == NOS_THREAD_SUSPENDED) {
                thread->state = (nOS_ThreadState)(thread->state | NOS_THREAD_SUSPENDED);
            }
#endif
            thread->event = NULL;
            thread->ext = NULL;
#if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
            thread->name = name;
#endif
            thread->error = (int)NOS_OK;
            thread->readyWait.payload = thread;
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
            thread->tout.payload = thread;
            thread->timeout = 0;
#endif
#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
            thread->node.payload = thread;
            nOS_AppendToList(&nOS_allThreadsList, &thread->node);
#endif
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
            thread->ext = (void*)entry;
            entry       = nOS_ThreadWrapper;
#endif
            nOS_InitContext(thread, stack, ssize
#ifdef NOS_USE_SEPARATE_CALL_STACK
                           ,cssize
#endif
                           ,entry, arg);
#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
            if (thread->state == NOS_THREAD_READY)
#endif
            {
                nOS_AppendThreadToReadyList(thread);
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                if (nOS_running) {
                    /* Verify if a highest prio thread is ready to run */
                    nOS_Schedule();
                }
#endif
            }

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_THREAD_DELETE_ENABLE > 0)
nOS_Error nOS_ThreadDelete (nOS_Thread *thread)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

    if (thread == NULL) {
        thread = nOS_runningThread;
    }

#if (NOS_CONFIG_SAFE > 0)
    /* Main thread can't be deleted */
    if (thread == &nOS_idleHandle) {
        err = NOS_E_INV_OBJ;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    if (thread == nOS_runningThread && nOS_lockNestingCounter > 0) {
        /* Can't switch context if scheduler is locked */
        err = NOS_E_LOCKED;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
            nOS_RemoveFromList(&nOS_allThreadsList, &thread->node);
#endif
            if (thread->state == NOS_THREAD_READY) {
                nOS_RemoveThreadFromReadyList(thread);
            }
            else if (thread->state & NOS_THREAD_WAITING_MASK) {
                if (thread->event != NULL) {
                    nOS_RemoveFromList(&thread->event->waitList, &thread->readyWait);
                }
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                if (thread->state & NOS_THREAD_WAIT_TIMEOUT) {
                    nOS_RemoveFromList(&nOS_timeoutThreadsList, &thread->tout);
                }
#endif
            }
            thread->state   = NOS_THREAD_STOPPED;
            thread->event   = NULL;
            thread->ext     = NULL;
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
            thread->timeout = 0;
#endif
            thread->error   = (int)NOS_E_DELETED;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);

        if (thread == nOS_runningThread) {
            /* Will never return */
            nOS_Schedule();
        }
    }

    return err;
}
#endif  /* NOS_CONFIG_THREAD_DELETE_ENABLE */

#if (NOS_CONFIG_THREAD_ABORT_ENABLE > 0)
nOS_Error nOS_ThreadAbort (nOS_Thread *thread)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (thread == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (thread == nOS_runningThread) {
        err = NOS_E_INV_OBJ;
    }
    else if (thread == &nOS_idleHandle) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        }
        else if (thread->state & NOS_THREAD_SUSPENDED) {
            err = NOS_E_INV_STATE;
        }
        else if ( !(thread->state & NOS_THREAD_WAITING_MASK) ) {
            err = NOS_E_INV_STATE;
        } else
#endif
        {
            nOS_WakeUpThread(thread, NOS_E_ABORT);
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
            /* Verify if a highest prio thread is ready to run */
            nOS_Schedule();
#endif
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_THREAD_ABORT_ENABLE */

#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
nOS_Error nOS_ThreadSuspend (nOS_Thread *thread)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

    if (thread == NULL) {
        thread = nOS_runningThread;
    }

#if (NOS_CONFIG_SAFE > 0)
    if (thread == &nOS_idleHandle) {
        err = NOS_E_INV_OBJ;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    if (thread == nOS_runningThread && nOS_lockNestingCounter > 0) {
        /* Can't switch context if scheduler is locked */
        err = NOS_E_LOCKED;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        }
        else if (thread->state & NOS_THREAD_SUSPENDED) {
            err = NOS_E_INV_STATE;
        } else
#endif
        {
            _SuspendThread(thread, NULL);
            if (thread == nOS_runningThread) {
                nOS_Schedule();
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_ThreadResume (nOS_Thread *thread)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (thread == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (thread == nOS_runningThread) {
        err = NOS_E_INV_OBJ;
    }
    else if (thread == &nOS_idleHandle) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        }
        else if ( !(thread->state & NOS_THREAD_SUSPENDED) ) {
            err = NOS_E_INV_STATE;
        } else
#endif
        {
            _ResumeThread(thread, NULL);
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
            /* Verify if a highest prio thread is ready to run */
            nOS_Schedule();
#endif
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
nOS_Error nOS_ThreadSuspendAll (void)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    /* Can't suspend all threads from any thread (except idle) when scheduler is locked */
    if ((nOS_lockNestingCounter > 0) && (nOS_runningThread != &nOS_idleHandle)) {
        err = NOS_E_LOCKED;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
        nOS_WalkInList(&nOS_allThreadsList, _SuspendThread, NULL);
        if (nOS_runningThread != &nOS_idleHandle) {
            nOS_Schedule();
        }
        nOS_LeaveCritical(sr);

        err = NOS_OK;
    }

    return err;
}

nOS_Error nOS_ThreadResumeAll (void)
{
    nOS_StatusReg   sr;

    nOS_EnterCritical(sr);
    nOS_WalkInList(&nOS_allThreadsList, _ResumeThread, NULL);
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
    /* Verify if a highest prio thread is ready to run */
    nOS_Schedule();
#endif
    nOS_LeaveCritical(sr);

    return NOS_OK;
}
#endif  /* NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE */
#endif  /* NOS_CONFIG_THREAD_SUSPEND_ENABLE */

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0) && (NOS_CONFIG_THREAD_SET_PRIO_ENABLE > 0)
nOS_Error nOS_ThreadSetPriority (nOS_Thread *thread, uint8_t prio)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

    if (thread == NULL) {
        thread = nOS_runningThread;
    }

#if (NOS_CONFIG_SAFE > 0)
    if (prio > NOS_CONFIG_HIGHEST_THREAD_PRIO) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (prio != thread->prio) {
                nOS_SetThreadPrio(thread, prio);
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                /* Verify if a highest prio thread is ready to run */
                nOS_Schedule();
#endif
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

int16_t nOS_ThreadGetPriority (nOS_Thread *thread)
{
    nOS_StatusReg   sr;
    int16_t         prio;

    if (thread == NULL) {
        thread = nOS_runningThread;
    }

    nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
    if (thread->state == NOS_THREAD_STOPPED) {
        prio = -1;
    } else
#endif
    {
        prio = (int16_t)thread->prio;
    }
    nOS_LeaveCritical(sr);

    return prio;
}
#endif  /* NOS_CONFIG_HIGHEST_THREAD_PRIO & NOS_CONFIG_THREAD_SET_PRIO_ENABLE */

#if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
const char* nOS_ThreadGetName (nOS_Thread *thread)
{
    nOS_StatusReg   sr;
    const char      *name;

    if (thread == NULL) {
        thread = nOS_runningThread;
    }

    nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
    if (thread->state == NOS_THREAD_STOPPED) {
        name = NULL;
    } else
#endif
    {
        name = thread->name;
    }
    nOS_LeaveCritical(sr);

    return name;
}

nOS_Error nOS_ThreadSetName (nOS_Thread *thread, const char *name)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (name == NULL) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        if (thread == NULL) {
            thread = nOS_runningThread;
        }

        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (thread->state == NOS_THREAD_STOPPED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            thread->name = name;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_THREAD_NAME_ENABLE */

#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
nOS_Error nOS_ThreadJoin (nOS_Thread *thread, int *ret, nOS_TickCounter timeout)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (thread == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
        if (thread->state & NOS_THREAD_FINISHED) {
            /* Thread already complete, return exit code */
            if (ret != NULL) {
                *ret = thread->error;
            }
            err = NOS_OK;
        }
        else if (timeout == NOS_NO_WAIT) {
            /* Calling thread can't wait. */
            err = NOS_E_AGAIN;
        }
        else {
            nOS_runningThread->ext = ret;
            /* Calling thread must wait for other thread to complete. */
            err = nOS_WaitForEvent((nOS_Event*)&thread->joined,
                                   NOS_THREAD_JOINING
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0)
                                  ,timeout
#elif (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                                  ,NOS_WAIT_INFINITE
#endif
                                  );
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_THREAD_JOIN_ENABLE */

#ifdef __cplusplus
}
#endif
