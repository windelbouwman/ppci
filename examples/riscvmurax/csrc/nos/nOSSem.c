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

#if (NOS_CONFIG_SEM_ENABLE > 0)
nOS_Error nOS_SemCreate (nOS_Sem *sem, nOS_SemCounter count, nOS_SemCounter max)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (sem == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (count > max) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (sem->e.type != NOS_EVENT_INVALID) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            nOS_CreateEvent((nOS_Event*)sem
#if (NOS_CONFIG_SAFE > 0)
                           ,NOS_EVENT_SEM
#endif
                           );
            sem->count = count;
            sem->max = max;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_SEM_DELETE_ENABLE > 0)
nOS_Error nOS_SemDelete (nOS_Sem *sem)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (sem == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (sem->e.type != NOS_EVENT_SEM) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            sem->count = 0;
            sem->max = 0;
            nOS_DeleteEvent((nOS_Event*)sem);

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif

nOS_Error nOS_SemTake (nOS_Sem *sem, nOS_TickCounter timeout)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (sem == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (sem->e.type != NOS_EVENT_SEM) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        if (sem->count > 0) {
            /* Sem available. */
            sem->count--;
            err = NOS_OK;
        }
        else if (timeout == NOS_NO_WAIT) {
            /* Calling thread can't wait. */
            err = NOS_E_AGAIN;
        }
        else {
            /* Calling thread must wait on sem. */
            err = nOS_WaitForEvent((nOS_Event*)sem,
                                   NOS_THREAD_TAKING_SEM
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

nOS_Error nOS_SemGive (nOS_Sem *sem)
{
    nOS_Error       err;
    nOS_StatusReg   sr;
    nOS_Thread      *thread;

#if (NOS_CONFIG_SAFE > 0)
    if (sem == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (sem->e.type != NOS_EVENT_SEM) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            thread = nOS_SendEvent((nOS_Event*)sem, NOS_OK);
            if (thread != NULL) {
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                /* Verify if a highest prio thread is ready to run */
                nOS_Schedule();
#endif
                err = NOS_OK;
            }
            /* No thread waiting for semaphore, can we increase count? */
            else if (sem->count < sem->max) {
                sem->count++;
                err = NOS_OK;
            }
            else if (sem->max > 0) {
                err = NOS_E_OVERFLOW;
            }
            else {
                /* No thread waiting to consume sem, inform producer */
                err = NOS_E_NO_CONSUMER;
            }
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

bool nOS_SemIsAvailable (nOS_Sem *sem)
{
    nOS_StatusReg   sr;
    bool            avail;

#if (NOS_CONFIG_SAFE > 0)
    if (sem == NULL) {
        avail = false;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (sem->e.type != NOS_EVENT_SEM) {
            avail = false;
        } else
#endif
        {
            avail = (sem->count > 0);
        }
        nOS_LeaveCritical(sr);
    }

    return avail;
}
#endif  /* NOS_CONFIG_SEM_ENABLE */

#ifdef __cplusplus
}
#endif
