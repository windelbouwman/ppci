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

#if (NOS_CONFIG_BARRIER_ENABLE > 0)
nOS_Error nOS_BarrierCreate (nOS_Barrier *barrier, uint8_t max)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (barrier == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (max == 0) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (barrier->e.type != NOS_EVENT_INVALID) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            nOS_CreateEvent((nOS_Event*)barrier
#if (NOS_CONFIG_SAFE > 0)
                           ,NOS_EVENT_BARRIER
#endif
                           );
            barrier->count = max;
            barrier->max   = max;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_BARRIER_DELETE_ENABLE > 0)
nOS_Error nOS_BarrierDelete (nOS_Barrier *barrier)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (barrier == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (barrier->e.type != NOS_EVENT_BARRIER) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            barrier->count = 0;
            barrier->max   = 0;
            nOS_DeleteEvent((nOS_Event*)barrier);

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif

nOS_Error nOS_BarrierWait (nOS_Barrier *barrier)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (barrier == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (barrier->e.type != NOS_EVENT_BARRIER) {
            /* Not a barrier event object */
            err = NOS_E_INV_OBJ;
        } else
#endif
        if (barrier->count == 1) {
            barrier->count = barrier->max;
            /* Wake up all threads waiting on barrier */
            nOS_BroadcastEvent((nOS_Event*)barrier, NOS_OK);

            err = NOS_OK;
        } else
#if (NOS_CONFIG_SAFE > 0)
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
        if (nOS_lockNestingCounter > 0) {
            /* Can't wait when scheduler is locked */
            err = NOS_E_LOCKED;
        } else
 #endif
        if (nOS_runningThread == &nOS_idleHandle) {
           /* Main thread can't wait */
            err = NOS_E_IDLE;
        } else
#endif
        {
            barrier->count--;
            /* Calling thread must wait for other threads. */
            err = nOS_WaitForEvent((nOS_Event*)barrier,
                                   NOS_THREAD_ON_BARRIER
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                                  ,NOS_WAIT_INFINITE
#endif
                                  );
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#endif  /* NOS_CONFIG_BARRIER_ENABLE */

#ifdef __cplusplus
}
#endif
