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

#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
#if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
 #if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
  static int _Thread (void *arg);
 #else
  static void _Thread (void *arg);
 #endif
#endif

#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
 static nOS_List                _list[NOS_CONFIG_SIGNAL_HIGHEST_PRIO+1];
 static uint8_t                 _listByPrio;
 #ifndef NOS_USE_CLZ
  static NOS_CONST uint8_t      _tableDeBruijn[8] = {
       0, 5, 1, 6, 4, 3, 2, 7
   };
 #endif
#else
 static nOS_List                _list;
#endif
#if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
 static nOS_Thread              _thread;
 #ifdef NOS_SIMULATED_STACK
  static nOS_Stack              _stack;
 #else
  static nOS_Stack              _stack[NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE];
 #endif
#endif

#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
 static inline nOS_Signal* _FindHighestPrio (void)
 {
     uint8_t prio;

     if (_listByPrio != 0) {
 #ifdef NOS_USE_CLZ
         prio = (uint8_t)(31 - _CLZ((uint32_t)_listByPrio));
 #else
         prio = _listByPrio;
         prio |= prio >> 1; // first round down to one less than a power of 2
         prio |= prio >> 2;
         prio |= prio >> 4;
         prio = (uint8_t)_tableDeBruijn[(uint8_t)(prio * 0x1d) >> 5];
 #endif

         return (nOS_Signal*)_list[prio].head->payload;
     }
     else {
         return (nOS_Signal*)NULL;
     }
 }
 static inline void _AppendToList (nOS_Signal *signal)
 {
     uint8_t prio = signal->prio;

     nOS_AppendToList(&_list[prio], &signal->node);
     _listByPrio |= (0x00000001UL << prio);
 }
 static inline void _RemoveFromList (nOS_Signal *signal)
 {
     uint8_t prio = signal->prio;

     nOS_RemoveFromList(&_list[prio], &signal->node);
     if (_list[prio].head == NULL) {
         _listByPrio &=~ (0x00000001UL << prio);
     }
 }
#else
 #define _FindHighestPrio()                 nOS_GetHeadOfList(&_list)
 #define _AppendToList(s)                   nOS_AppendToList(&_list, &(s)->node)
 #define _RemoveFromList(s)                 nOS_RemoveFromList(&_list, &(s)->node)
#endif

#if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
static int _Thread (void *arg)
#else
static void _Thread (void *arg)
#endif
{
    nOS_StatusReg   sr;

    NOS_UNUSED(arg);

    while (1) {
        nOS_SignalProcess();

        nOS_EnterCritical(sr);
        if (_FindHighestPrio() == NULL) {
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
#endif  /* NOS_CONFIG_SIGNAL_THREAD_ENABLE */

void nOS_InitSignal (void)
{
#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
    uint8_t i;
    for (i = 0; i < NOS_CONFIG_SIGNAL_HIGHEST_PRIO; i++) {
        nOS_InitList(&_list[i]);
    }
#else
    nOS_InitList(&_list);
#endif
#if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
    nOS_ThreadCreate(&_thread,
                     _Thread,
                     NULL
 #ifdef NOS_SIMULATED_STACK
                    ,&_stack
 #else
                    ,_stack
 #endif
                    ,NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE
 #ifdef NOS_USE_SEPARATE_CALL_STACK
                    ,NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE
 #endif
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                    ,NOS_CONFIG_SIGNAL_THREAD_PRIO
 #endif
 #if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
                    ,NOS_THREAD_READY
 #endif
 #if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
                    ,"nOS_Signal"
 #endif
                    );
#endif
}

void nOS_SignalProcess (void)
{
    nOS_StatusReg       sr;
    nOS_Signal          *signal  = NULL;
    nOS_SignalCallback  callback = NULL;
    void                *arg     = NULL;

    nOS_EnterCritical(sr);
    signal = (nOS_Signal *)_FindHighestPrio();
    if (signal != NULL) {
        if (signal->state & NOS_SIGNAL_RAISED) {
            signal->state = (nOS_SignalState)(signal->state &~ NOS_SIGNAL_RAISED);
            _RemoveFromList(signal);

            callback = signal->callback;
            arg      = signal->arg;
        }
    }
    nOS_LeaveCritical(sr);

    if (callback != NULL) {
        callback(signal, arg);
    }
}

nOS_Error nOS_SignalCreate (nOS_Signal *signal,
                            nOS_SignalCallback callback
#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
                            ,uint8_t prio
#endif
                            )
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (callback == NULL) {
        err = NOS_E_INV_VAL;
    } else
 #if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
    if (prio > NOS_CONFIG_SIGNAL_HIGHEST_PRIO) {
        err = NOS_E_INV_PRIO;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state != NOS_SIGNAL_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            signal->state        = NOS_SIGNAL_CREATED;
            signal->callback     = callback;
#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
            signal->prio         = prio;
#endif
            signal->node.payload = (void *)signal;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_SIGNAL_DELETE_ENABLE > 0)
nOS_Error nOS_SignalDelete (nOS_Signal *signal)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state == NOS_SIGNAL_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (signal->state & NOS_SIGNAL_RAISED) {
                _RemoveFromList(signal);
            }
            signal->state           = NOS_SIGNAL_DELETED;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif /* NOS_CONFIG_SIGNAL_DELETE_ENABLE */

nOS_Error nOS_SignalSend (nOS_Signal *signal, void *arg)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state == NOS_SIGNAL_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        if (signal->state & NOS_SIGNAL_RAISED) {
            err = NOS_E_OVERFLOW;
        }
        else {
            signal->state = (nOS_SignalState)(signal->state | NOS_SIGNAL_RAISED);
            signal->arg   = arg;
            _AppendToList(signal);

#if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
            if (_thread.state == (NOS_THREAD_READY | NOS_THREAD_ON_HOLD)) {
                nOS_WakeUpThread(&_thread, NOS_OK);
            }
#endif
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_SignalSetCallback (nOS_Signal *signal, nOS_SignalCallback callback)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (callback == NULL) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state == NOS_SIGNAL_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            signal->callback = callback;

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
nOS_Error nOS_SignalSetPrio (nOS_Signal *signal, uint8_t prio)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (prio > NOS_CONFIG_SIGNAL_HIGHEST_PRIO) {
        err = NOS_E_INV_PRIO;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state == NOS_SIGNAL_DELETED) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            if (signal->state & NOS_SIGNAL_RAISED) {
                _RemoveFromList(signal);
            }
            signal->prio = prio;
            if (signal->state & NOS_SIGNAL_RAISED) {
                _AppendToList(signal);
            }

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_SIGNAL_HIGHEST_PRIO */

bool nOS_SignalIsRaised (nOS_Signal *signal)
{
    nOS_StatusReg   sr;
    bool            raised;

#if (NOS_CONFIG_SAFE > 0)
    if (signal == NULL) {
        raised = false;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (signal->state == NOS_SIGNAL_DELETED) {
            raised = false;
        } else
#endif
        {
            raised = (signal->state & NOS_SIGNAL_RAISED) == NOS_SIGNAL_RAISED;
        }
        nOS_LeaveCritical(sr);
    }

    return raised;
}
#endif  /* NOS_CONFIG_SIGNAL_ENABLE */

#ifdef __cplusplus
}
#endif
