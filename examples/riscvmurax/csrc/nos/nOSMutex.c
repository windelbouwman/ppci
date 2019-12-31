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

#if (NOS_CONFIG_MUTEX_ENABLE > 0)
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
 static void _TestPrioHighest (void *payload, void *arg)
 {
    nOS_Thread      *thread  = (nOS_Thread*)payload;
    uint8_t         *prio    = (uint8_t*)arg;

    if (*prio < thread->prio) {
        *prio = thread->prio;
    }
 }

 static uint8_t _FindHighestPrioWaiting(nOS_Mutex *mutex)
 {
    uint8_t prio = 0;

    nOS_WalkInList(&mutex->e.waitList, _TestPrioHighest, &prio);

    return prio;
 }
 #endif

nOS_Error nOS_MutexCreate (nOS_Mutex *mutex,
                           nOS_MutexType type
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                           ,uint8_t prio
#endif
                           )
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if ((type != NOS_MUTEX_NORMAL) && (type != NOS_MUTEX_RECURSIVE)) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_INVALID) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            nOS_CreateEvent((nOS_Event*)mutex
#if (NOS_CONFIG_SAFE > 0)
                           ,NOS_EVENT_MUTEX
#endif
                           );
            mutex->owner = NULL;
            mutex->type = type;
            mutex->count = 0;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
            mutex->prio = prio;
            mutex->backup = 0;
#endif
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_MUTEX_DELETE_ENABLE > 0)
nOS_Error nOS_MutexDelete (nOS_Mutex *mutex)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_MUTEX) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            mutex->owner = NULL;
            mutex->count = 0;
            nOS_DeleteEvent((nOS_Event*)mutex);

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif

nOS_Error nOS_MutexLock (nOS_Mutex *mutex, nOS_TickCounter timeout)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (nOS_isrNestingCounter > 0) {
        /* Can't lock mutex from ISR */
        err = NOS_E_ISR;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_MUTEX) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        if (mutex->owner == NULL) {
            /* Mutex available? Reserve it for calling thread */
            mutex->count++;
            mutex->owner = nOS_runningThread;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
            mutex->backup = nOS_runningThread->prio;
            if (mutex->prio != NOS_MUTEX_PRIO_INHERIT) {
                if (nOS_runningThread->prio < mutex->prio) {
                    nOS_SetThreadPrio(nOS_runningThread, mutex->prio);
                }
            }
#endif
            err = NOS_OK;
        }
        else if (mutex->owner == nOS_runningThread) {
            /* Mutex owner relock it? */
            if (mutex->type == NOS_MUTEX_RECURSIVE && mutex->count < NOS_MUTEX_COUNT_MAX) {
                mutex->count++;
                err = NOS_OK;
            }
            else {
                /* Can't lock multiple times binary mutex or recursive mutex already at maximum count */
                err = NOS_E_OVERFLOW;
            }
        }
        else {
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
            /* If current thread can ask to lock mutex, maybe is prio is higher than mutex owner prio. */
            if (mutex->prio == NOS_MUTEX_PRIO_INHERIT) {
                if (mutex->owner->prio < nOS_runningThread->prio) {
                    nOS_SetThreadPrio(mutex->owner, nOS_runningThread->prio);
                }
            }
#endif

            if (timeout == NOS_NO_WAIT) {
                /* Calling thread can't wait? Try again. */
                err = NOS_E_AGAIN;
            }
            else {
                /* Calling thread must wait on mutex. */
                err = nOS_WaitForEvent((nOS_Event*)mutex,
                                       NOS_THREAD_LOCKING_MUTEX
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0)
                                      ,timeout
#elif (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                                      ,NOS_WAIT_INFINITE
#endif
                                      );
            }
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_MutexUnlock (nOS_Mutex *mutex)
{
    nOS_Error       err;
    nOS_StatusReg   sr;
    nOS_Thread      *thread;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
    uint8_t         prio;
#endif

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (nOS_isrNestingCounter > 0) {
        /* Can't unlock mutex from ISR */
        err = NOS_E_ISR;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_MUTEX) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        if (mutex->owner == NULL) {
            err = NOS_E_UNDERFLOW;
        }
        else if (mutex->owner != nOS_runningThread) {
            err = NOS_E_OWNER;
        }
        else {
            if (mutex->count == 1) {
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                nOS_SetThreadPrio(mutex->owner, mutex->backup);
#endif
                thread = nOS_SendEvent((nOS_Event*)mutex, NOS_OK);
                if (thread != NULL) {
                    mutex->owner = thread;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                    mutex->backup = thread->prio;
                    if (mutex->prio != NOS_MUTEX_PRIO_INHERIT) {
                        if (thread->prio < mutex->prio) {
                            nOS_SetThreadPrio(thread, mutex->prio);
                        }
                    }
                    /* If mutex is using priority inheritance, verify if there is other threads
                     * in waiting list. If yes, then search for highest priority of threads in
                     * waiting list and set new mutex owner to this priority if needed. */
                    else if (mutex->e.waitList.head != NULL) {
                        prio = _FindHighestPrioWaiting(mutex);
                        if (thread->prio < prio) {
                            nOS_SetThreadPrio(thread, prio);
                        }
                    }
#endif
                }
                else {
                    mutex->count = 0;
                    mutex->owner = NULL;
                }
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0) && (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                /* Verify if a highest prio thread is ready to run */
                nOS_Schedule();
#endif
            } else {
                mutex->count--;
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

bool nOS_MutexIsLocked (nOS_Mutex *mutex)
{
    nOS_StatusReg   sr;
    bool            locked;

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        locked = false;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_MUTEX) {
            locked = false;
        } else
#endif
        {
            locked = (mutex->owner != NULL);
        }
        nOS_LeaveCritical(sr);
    }

    return locked;
}

nOS_Thread* nOS_MutexGetOwner (nOS_Mutex *mutex)
{
    nOS_StatusReg   sr;
    nOS_Thread      *owner;

#if (NOS_CONFIG_SAFE > 0)
    if (mutex == NULL) {
        owner = NULL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mutex->e.type != NOS_EVENT_MUTEX) {
            owner = NULL;
        } else
#endif
        {
            owner = mutex->owner;
        }
        nOS_LeaveCritical(sr);
    }

    return owner;
}
#endif  /* NOS_CONFIG_MUTEX_ENABLE */

#ifdef __cplusplus
}
#endif
