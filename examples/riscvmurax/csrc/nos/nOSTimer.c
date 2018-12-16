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

#if (NOS_CONFIG_TIMER_ENABLE > 0)
typedef struct _TickContext
{
    nOS_TickCounter ticks;
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
    bool            triggered;
#endif
} _TickContext;

#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
 #if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
  static int _Thread (void *arg);
 #else
  static void _Thread (void *arg);
 #endif
#endif
static  void    _Tick       (void *payload, void *arg);

static nOS_List                 _activeList;
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
 static nOS_List                _triggeredList[NOS_CONFIG_TIMER_HIGHEST_PRIO+1];
 static uint8_t                 _triggeredListByPrio;
 #ifndef NOS_USE_CLZ
  static NOS_CONST uint8_t      _tableDeBruijn[8] = {
       0, 5, 1, 6, 4, 3, 2, 7
   };
 #endif
#else
 static nOS_List                _triggeredList;
#endif
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
 static nOS_Thread              _thread;
 #ifdef NOS_SIMULATED_STACK
  static nOS_Stack              _stack;
 #else
  static nOS_Stack              _stack[NOS_CONFIG_TIMER_THREAD_STACK_SIZE];
 #endif
#endif
static nOS_TimerCounter         _tickCounter;

#define _AppendToActiveList(t)          nOS_AppendToList(&_activeList, &(t)->node)
#define _RemoveFromActiveList(t)        nOS_RemoveFromList(&_activeList, &(t)->node)
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
 static inline nOS_Timer* _FindTriggeredHighestPrio (void)
 {
     uint8_t prio;

     if (_triggeredListByPrio != 0) {
 #ifdef NOS_USE_CLZ
         prio = (uint8_t)(31 - _CLZ((uint32_t)_triggeredListByPrio));
 #else
         prio = _triggeredListByPrio;
         prio |= prio >> 1; // first round down to one less than a power of 2
         prio |= prio >> 2;
         prio |= prio >> 4;
         prio = (uint8_t)_tableDeBruijn[(uint8_t)(prio * 0x1d) >> 5];
 #endif

         return (nOS_Timer*)_triggeredList[prio].head->payload;
     }
     else {
         return (nOS_Timer*)NULL;
     }
 }
 static inline void _AppendToTriggeredList (nOS_Timer *timer)
 {
     uint8_t prio = timer->prio;

     nOS_AppendToList(&_triggeredList[prio], &timer->trig);
     _triggeredListByPrio |= (0x00000001UL << prio);
 }
 static inline void _RemoveFromTriggeredList (nOS_Timer *timer)
 {
     uint8_t prio = timer->prio;

     nOS_RemoveFromList(&_triggeredList[prio], &timer->trig);
     if (_triggeredList[prio].head == NULL) {
         _triggeredListByPrio &=~ (0x00000001UL << prio);
     }
 }
#else
 #define _FindTriggeredHighestPrio()    nOS_GetHeadOfList(&_triggeredList)
 #define _AppendToTriggeredList(t)      nOS_AppendToList(&_triggeredList, &(t)->trig)
 #define _RemoveFromTriggeredList(t)    nOS_RemoveFromList(&_triggeredList, &(t)->trig)
#endif

#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
static int _Thread (void *arg)
#else
static void _Thread (void *arg)
#endif
{
    nOS_StatusReg   sr;

    NOS_UNUSED(arg);

    while (true) {
        nOS_TimerProcess();

        nOS_EnterCritical(sr);
        if (_FindTriggeredHighestPrio() == NULL) {
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
    nOS_Timer           *timer  = (nOS_Timer *)payload;
    _TickContext        *ctx    = (_TickContext *)arg;
    nOS_TimerCounter    overflow;

    if ((timer->count - _tickCounter) <= ctx->ticks) {
        overflow = 1;
        if (((nOS_TimerMode)timer->state & NOS_TIMER_MODE) == NOS_TIMER_FREE_RUNNING) {
            /* Free running timer */
            overflow += ((ctx->ticks - (timer->count - _tickCounter)) / timer->reload);
            timer->count += (overflow * timer->reload);
        }
        else {
            /* One-shot timer */
            timer->state = (nOS_TimerState)(timer->state &~ NOS_TIMER_RUNNING);
            _RemoveFromActiveList(timer);
        }
        if (timer->overflow == 0) {
            _AppendToTriggeredList(timer);
        }
        if ((NOS_TIMER_COUNT_MAX - timer->overflow) < overflow) {
            timer->overflow = NOS_TIMER_COUNT_MAX;
        } else {
            timer->overflow += overflow;
        }
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
        ctx->triggered = true;
#endif
    }
}

void nOS_InitTimer(void)
{
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
    uint8_t i;
    for (i = 0; i < NOS_CONFIG_TIMER_HIGHEST_PRIO; i++) {
        nOS_InitList(&_triggeredList[i]);
    }
#else
    nOS_InitList(&_triggeredList);
#endif
    _tickCounter = 0;
    nOS_InitList(&_activeList);
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
    nOS_ThreadCreate(&_thread,
                     _Thread,
                     NULL
 #ifdef NOS_SIMULATED_STACK
                    ,&_stack
 #else
                    ,_stack
 #endif
                    ,NOS_CONFIG_TIMER_THREAD_STACK_SIZE
 #ifdef NOS_USE_SEPARATE_CALL_STACK
                    ,NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE
 #endif
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                    ,NOS_CONFIG_TIMER_THREAD_PRIO
 #endif
 #if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
                    ,NOS_THREAD_READY
 #endif
 #if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
                    ,"nOS_Timer"
 #endif
                    );
#endif
}

void nOS_TimerTick (nOS_TickCounter ticks)
{
    nOS_StatusReg   sr;
    _TickContext    ctx;

    ctx.ticks = ticks;
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
    ctx.triggered = false;
#endif

    nOS_EnterCritical(sr);
    nOS_WalkInList(&_activeList, _Tick, &ctx);
#if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
    if (ctx.triggered && (_thread.state == (NOS_THREAD_READY | NOS_THREAD_ON_HOLD))) {
        nOS_WakeUpThread(&_thread, NOS_OK);
    }
#endif
    _tickCounter += ticks;
    nOS_LeaveCritical(sr);
}

void nOS_TimerProcess (void)
{
    nOS_StatusReg       sr;
    nOS_Timer           *timer;
    nOS_TimerCallback   callback = NULL;
    void                *arg;

    nOS_EnterCritical(sr);
    timer = (nOS_Timer*)_FindTriggeredHighestPrio();
    if (timer != NULL) {
        timer->overflow--;
        if (timer->overflow == 0) {
            _RemoveFromTriggeredList(timer);
        }
        else {
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
            nOS_RotateList(&_triggeredList[timer->prio]);
#else
            nOS_RotateList(&_triggeredList);
#endif
        }

        /* Call callback function outside of critical section */
        callback = timer->callback;
        arg      = timer->arg;
    }
    nOS_LeaveCritical(sr);

    if (callback != NULL) {
        callback(timer, arg);
    }
}

nOS_Error nOS_TimerCreate (nOS_Timer *timer,
                           nOS_TimerCallback callback,
                           void *arg,
                           nOS_TimerCounter reload,
                           nOS_TimerMode mode
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
                          ,uint8_t prio
#endif
                          )
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if ((mode != NOS_TIMER_FREE_RUNNING) && (mode != NOS_TIMER_ONE_SHOT)) {
        err = NOS_E_INV_VAL;
    } else
 #if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
    if (prio > NOS_CONFIG_TIMER_HIGHEST_PRIO) {
        err = NOS_E_INV_PRIO;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state != NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            timer->count        = 0;
            timer->reload       = reload;
            timer->state        = (nOS_TimerState)(NOS_TIMER_CREATED | (nOS_TimerState)(mode & NOS_TIMER_MODE));
            timer->overflow     = 0;
            timer->callback     = callback;
            timer->arg          = arg;
#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
            timer->prio         = prio;
#endif
            timer->node.payload = (void *)timer;
            timer->trig.payload = (void *)timer;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_TIMER_DELETE_ENABLE > 0)
nOS_Error nOS_TimerDelete (nOS_Timer *timer)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if ((timer->state & (NOS_TIMER_RUNNING | NOS_TIMER_PAUSED)) == NOS_TIMER_RUNNING) {
                _RemoveFromActiveList(timer);
            }
            timer->state = NOS_TIMER_DELETED;
            if (timer->overflow > 0) {
                timer->overflow = 0;
                _RemoveFromTriggeredList(timer);
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_TIMER_DELETE_ENABLE */

nOS_Error nOS_TimerStart (nOS_Timer *timer)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        }
        else if (timer->reload == 0) {
            err = NOS_E_INV_VAL;
        } else
#endif
        {
            if ( !(timer->state & NOS_TIMER_RUNNING) ) {
                timer->state = (nOS_TimerState)(timer->state | NOS_TIMER_RUNNING);
                _AppendToActiveList(timer);
            }
            timer->count = _tickCounter + timer->reload;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerStop (nOS_Timer *timer, bool instant)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if ((timer->state & (NOS_TIMER_RUNNING | NOS_TIMER_PAUSED)) == NOS_TIMER_RUNNING) {
                _RemoveFromActiveList(timer);
            }
            timer->state = (nOS_TimerState)(timer->state &~ (NOS_TIMER_RUNNING | NOS_TIMER_PAUSED));
            if ((timer->overflow > 0) && instant) {
                timer->overflow = 0;
                _RemoveFromTriggeredList(timer);
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerRestart (nOS_Timer *timer, nOS_TimerCounter reload)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (reload == 0) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if ( !(timer->state & NOS_TIMER_RUNNING) ) {
                timer->state  = (nOS_TimerState)(timer->state | NOS_TIMER_RUNNING);
                _AppendToActiveList(timer);
            }
            timer->reload = reload;
            timer->count  = _tickCounter + reload;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerPause (nOS_Timer *timer)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if ((timer->state & (NOS_TIMER_RUNNING | NOS_TIMER_PAUSED)) == NOS_TIMER_RUNNING) {
                timer->state = (nOS_TimerState)(timer->state | NOS_TIMER_PAUSED);
                _RemoveFromActiveList(timer);
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerContinue (nOS_Timer *timer)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (timer->state & NOS_TIMER_PAUSED) {
                timer->state = (nOS_TimerState)(timer->state &~ NOS_TIMER_PAUSED);
                _AppendToActiveList(timer);
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerSetReload (nOS_Timer *timer, nOS_TimerCounter reload)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (reload == 0) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            timer->reload = reload;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerSetCallback (nOS_Timer *timer, nOS_TimerCallback callback, void *arg)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            timer->callback = callback;
            timer->arg      = arg;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_TimerSetMode (nOS_Timer *timer, nOS_TimerMode mode)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if ((mode != NOS_TIMER_FREE_RUNNING) && (mode != NOS_TIMER_ONE_SHOT)) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            timer->state = (nOS_TimerState)(((nOS_TimerMode)timer->state &~ NOS_TIMER_MODE) | mode);

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
nOS_Error nOS_TimerSetPrio (nOS_Timer *timer, uint8_t prio)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (prio > NOS_CONFIG_TIMER_HIGHEST_PRIO) {
        err = NOS_E_INV_PRIO;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (timer->overflow > 0) {
                _RemoveFromTriggeredList(timer);
            }
            timer->prio = prio;
            if (timer->overflow > 0) {
                _AppendToTriggeredList(timer);
            }
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif

bool nOS_TimerIsRunning (nOS_Timer *timer)
{
    nOS_StatusReg   sr;
    bool            running;

#if (NOS_CONFIG_SAFE > 0)
    if (timer == NULL) {
        running = false;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (timer->state == NOS_TIMER_DELETED) {
            running = false;
        } else
#endif
        {
            running = (timer->state & (NOS_TIMER_RUNNING | NOS_TIMER_PAUSED)) == NOS_TIMER_RUNNING;
        }
        nOS_LeaveCritical(sr);
    }

    return running;
}
#endif  /* NOS_CONFIG_TIMER_ENABLE */

#ifdef __cplusplus
}
#endif
