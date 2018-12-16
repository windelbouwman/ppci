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

#if (NOS_CONFIG_TIME_ENABLE > 0) && (NOS_CONFIG_ALARM_ENABLE > 0)
typedef struct _TickContext
{
    nOS_Time    time;
#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
    bool        triggered;
#endif
} _TickContext;

#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
 #if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
  static int _Thread (void *arg);
 #else
  static void _Thread (void *arg);
 #endif
#endif
static  void    _Tick       (void *payload, void *arg);

static nOS_List         _waitingList;
static nOS_List         _triggeredList;
#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
 static nOS_Thread      _thread;
 #ifdef NOS_SIMULATED_STACK
  static nOS_Stack      _stack;
 #else
  static nOS_Stack      _stack[NOS_CONFIG_ALARM_THREAD_STACK_SIZE];
 #endif
#endif

#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
static int _Thread (void *arg)
#else
static void _Thread (void *arg)
#endif
{
    nOS_StatusReg   sr;

    NOS_UNUSED(arg);

    while (true) {
        nOS_AlarmProcess();

        nOS_EnterCritical(sr);
        if (nOS_GetHeadOfList(&_triggeredList) == NULL) {
            nOS_WaitForEvent(NULL,
                             NOS_THREAD_ON_HOLD
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                            ,NOS_WAIT_INFINITE
#endif
                            );
        }
        nOS_LeaveCritical(sr);

#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
        if (false) break; /* Remove "statement is unreachable" warning */
    }

    return 0;
#else
    }
#endif
}
#endif

/* Called from critical section */
static void _Tick (void *payload, void *arg)
{
    nOS_Alarm       *alarm  = (nOS_Alarm *)payload;
    _TickContext    *ctx    = (_TickContext *)arg;

    if (ctx->time >= alarm->time) {
        nOS_RemoveFromList(&_waitingList, &alarm->node);
        alarm->state = (nOS_AlarmState)(alarm->state &~ NOS_ALARM_WAITING);

        alarm->state = (nOS_AlarmState)(alarm->state | NOS_ALARM_TRIGGERED);
        nOS_AppendToList(&_triggeredList, &alarm->node);

#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
        ctx->triggered = true;
#endif
    }
}

void nOS_InitAlarm(void)
{
    nOS_InitList(&_waitingList);
    nOS_InitList(&_triggeredList);
#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
    nOS_ThreadCreate(&_thread,
                     _Thread,
                     NULL
 #ifdef NOS_SIMULATED_STACK
                    ,&_stack
 #else
                    ,_stack
 #endif
                    ,NOS_CONFIG_ALARM_THREAD_STACK_SIZE
 #ifdef NOS_USE_SEPARATE_CALL_STACK
                    ,NOS_CONFIG_ALARM_THREAD_CALL_STACK_SIZE
 #endif
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                    ,NOS_CONFIG_ALARM_THREAD_PRIO
 #endif
 #if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
                    ,NOS_THREAD_READY
 #endif
 #if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
                    ,"nOS_Alarm"
 #endif
                    );
#endif
}

/* Called from critical section if NOS_CONFIG_ALARM_TICK_ENABLE is enabled */
void nOS_AlarmTick (void)
{
#if (NOS_CONFIG_ALARM_TICK_ENABLE == 0)
    nOS_StatusReg   sr;
#endif
    _TickContext    ctx;

#if (NOS_CONFIG_ALARM_TICK_ENABLE == 0)
    nOS_EnterCritical(sr);
#endif
    ctx.time = nOS_TimeGet();
#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
    ctx.triggered = false;
#endif
    nOS_WalkInList(&_waitingList, _Tick, &ctx);
#if (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
    if (ctx.triggered && (_thread.state == (NOS_THREAD_READY | NOS_THREAD_ON_HOLD))) {
        nOS_WakeUpThread(&_thread, NOS_OK);
    }
#endif
#if (NOS_CONFIG_ALARM_TICK_ENABLE == 0)
    nOS_LeaveCritical(sr);
#endif
}

void nOS_AlarmProcess (void)
{
    nOS_StatusReg       sr;
    nOS_Alarm           *alarm;
    nOS_AlarmCallback   callback = NULL;
    void                *arg;

    nOS_EnterCritical(sr);
    alarm = (nOS_Alarm*)nOS_GetHeadOfList(&_triggeredList);
    if (alarm != NULL) {
        nOS_RemoveFromList(&_triggeredList, &alarm->node);
        alarm->state = (nOS_AlarmState)(alarm->state &~ NOS_ALARM_TRIGGERED);

        /* Call callback function outside of critical section */
        callback = alarm->callback;
        arg      = alarm->arg;
    }
    nOS_LeaveCritical(sr);

    if (callback != NULL) {
        callback(alarm, arg);
    }
}

nOS_Error nOS_AlarmCreate (nOS_Alarm *alarm, nOS_AlarmCallback callback, void *arg, nOS_Time time)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (alarm == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (alarm->state != NOS_ALARM_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            alarm->state    = NOS_ALARM_CREATED;
            alarm->callback = callback;
            alarm->arg      = arg;
            alarm->time     = time;
            alarm->node.payload = (void *)alarm;
            if (time <= nOS_TimeGet()) {
                alarm->state = (nOS_AlarmState)(alarm->state | NOS_ALARM_TRIGGERED);
                nOS_AppendToList(&_triggeredList, &alarm->node);
            }
            else {
                alarm->state = (nOS_AlarmState)(alarm->state | NOS_ALARM_WAITING);
                nOS_AppendToList(&_waitingList, &alarm->node);
            }

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_ALARM_DELETE_ENABLE > 0)
nOS_Error nOS_AlarmDelete (nOS_Alarm *alarm)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (alarm == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (alarm->state == NOS_ALARM_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (alarm->state & NOS_ALARM_WAITING) {
                nOS_RemoveFromList(&_waitingList, &alarm->node);
            }
            else if (alarm->state & NOS_ALARM_TRIGGERED) {
                nOS_RemoveFromList(&_triggeredList, &alarm->node);
            }
            alarm->state = NOS_ALARM_DELETED;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif

nOS_Error nOS_AlarmSetTime (nOS_Alarm *alarm, nOS_Time time)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (alarm == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (alarm->state == NOS_ALARM_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (time != alarm->time) {
                if (alarm->state & NOS_ALARM_WAITING) {
                    nOS_RemoveFromList(&_waitingList, &alarm->node);
                    alarm->state = (nOS_AlarmState)(alarm->state &~ NOS_ALARM_WAITING);
                }
                else if (alarm->state & NOS_ALARM_TRIGGERED) {
                    nOS_RemoveFromList(&_triggeredList, &alarm->node);
                    alarm->state = (nOS_AlarmState)(alarm->state &~ NOS_ALARM_TRIGGERED);
                }

                alarm->time     = time;

                if (time <= nOS_TimeGet()) {
                    alarm->state = (nOS_AlarmState)(alarm->state | NOS_ALARM_TRIGGERED);
                    nOS_AppendToList(&_triggeredList, &alarm->node);
                }
                else {
                    alarm->state = (nOS_AlarmState)(alarm->state | NOS_ALARM_WAITING);
                    nOS_AppendToList(&_waitingList, &alarm->node);
                }
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_AlarmSetCallback (nOS_Alarm *alarm, nOS_AlarmCallback callback, void *arg)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (alarm == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (alarm->state == NOS_ALARM_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            alarm->callback = callback;
            alarm->arg      = arg;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_TIME_ENABLE && NOS_CONFIG_ALARM_ENABLE */

#ifdef __cplusplus
}
#endif
