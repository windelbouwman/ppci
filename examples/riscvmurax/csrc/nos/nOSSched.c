/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#define NOS_GLOBALS
#define NOS_PRIVATE
#include "nOS.h"

#ifdef __cplusplus
extern "C" {
#endif

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
 #ifdef NOS_32_BITS_SCHEDULER
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 32)
   static uint32_t              _readyThreadByPrio;
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
   static uint32_t              _readyThreadByGroup;
   static uint32_t              _readyThreadByPrio[((NOS_CONFIG_HIGHEST_THREAD_PRIO+31)/32)];
  #endif
  #ifndef NOS_USE_CLZ
   static NOS_CONST uint8_t     _tableDeBruijn[32] = {
       0, 9, 1, 10, 13, 21, 2, 29, 11, 14, 16, 18, 22, 25, 3, 30,
       8, 12, 20, 28, 15, 17, 24, 7, 19, 27, 23, 6, 26, 5, 4, 31
   };
  #endif
 #elif defined(NOS_16_BITS_SCHEDULER)
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
   static uint16_t              _readyThreadByPrio;
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
   static uint16_t              _readyThreadByGroup;
   static uint16_t              _readyThreadByPrio[((NOS_CONFIG_HIGHEST_THREAD_PRIO+15)/16)];
  #endif
  static NOS_CONST uint8_t      _tableDeBruijn[16] = {
      0, 7, 1, 13, 8, 10, 2, 14, 6, 12, 9, 5, 11, 4, 3, 15
  };
 #else
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 8)
   static uint8_t               _readyThreadByPrio;
   static NOS_CONST uint8_t     _tableDeBruijn[8] = {
       0, 5, 1, 6, 4, 3, 2, 7
   };
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
   static uint16_t              _readyThreadByPrio;
   static NOS_CONST uint8_t     _tableDeBruijn[16] = {
       0, 7, 1, 13, 8, 10, 2, 14, 6, 12, 9, 5, 11, 4, 3, 15
   };
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 64)
   static uint8_t               _readyThreadByGroup;
   static uint8_t               _readyThreadByPrio[((NOS_CONFIG_HIGHEST_THREAD_PRIO+7)/8)];
   static NOS_CONST uint8_t     _tableDeBruijn[8] = {
       0, 5, 1, 6, 4, 3, 2, 7
   };
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
   static uint16_t              _readyThreadByGroup;
   static uint16_t              _readyThreadByPrio[((NOS_CONFIG_HIGHEST_THREAD_PRIO+15)/16)];
   static NOS_CONST uint8_t     _tableDeBruijn[16] = {
       0, 7, 1, 13, 8, 10, 2, 14, 6, 12, 9, 5, 11, 4, 3, 15
   };
  #endif
 #endif
#endif

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
 #ifdef NOS_32_BITS_SCHEDULER
  #ifdef NOS_USE_CLZ
   #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 32)
    nOS_Thread* nOS_FindHighPrioThread(void)
    {
        uint32_t    prio;

        prio = (31 - _CLZ(_readyThreadByPrio));

        return (nOS_Thread*)nOS_readyThreadsList[prio].head->payload;
    }
   #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
    nOS_Thread* nOS_FindHighPrioThread(void)
    {
        uint32_t    group;
        uint32_t    prio;

        group   = (31 - _CLZ(_readyThreadByGroup));
        prio    = (31 - _CLZ(_readyThreadByPrio[group]));

        return (nOS_Thread*)nOS_readyThreadsList[(group << 5) | prio].head->payload;
    }
   #endif
  #else
   #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 32)
    nOS_Thread* nOS_FindHighPrioThread(void)
    {
        uint32_t    prio;

        prio = _readyThreadByPrio;
        prio |= prio >> 1; // first round down to one less than a power of 2
        prio |= prio >> 2;
        prio |= prio >> 4;
        prio |= prio >> 8;
        prio |= prio >> 16;
        prio = (uint32_t)_tableDeBruijn[(uint32_t)(prio * 0x07c4acddUL) >> 27];

        return (nOS_Thread*)nOS_readyThreadsList[prio].head->payload;
    }
   #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
    nOS_Thread* nOS_FindHighPrioThread(void)
    {
        uint32_t    group;
        uint32_t    prio;

        group = _readyThreadByGroup;
        group |= group >> 1;
        group |= group >> 2;
        group |= group >> 4;
        group |= group >> 8;
        group |= group >> 16;
        group = (uint32_t)_tableDeBruijn[(uint32_t)(group * 0x07c4acddUL) >> 27];

        prio = _readyThreadByPrio[group];
        prio |= prio >> 1; // first round down to one less than a power of 2
        prio |= prio >> 2;
        prio |= prio >> 4;
        prio |= prio >> 8;
        prio |= prio >> 16;
        prio = (uint32_t)_tableDeBruijn[(uint32_t)(prio * 0x07c4acddUL) >> 27];

        return (nOS_Thread*)nOS_readyThreadsList[(group << 5) | prio].head->payload;
    }
   #endif
  #endif
 #elif defined(NOS_16_BITS_SCHEDULER)
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint16_t    prio;

       prio = _readyThreadByPrio;
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio |= prio >> 8;
       prio = (uint16_t)_tableDeBruijn[(uint16_t)(prio * 0xf2d) >> 12];

       return (nOS_Thread*)nOS_readyThreadsList[prio].head->payload;
   }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint16_t    group;
       uint16_t    prio;

       group = _readyThreadByGroup;
       group |= group >> 1; // first round down to one less than a power of 2
       group |= group >> 2;
       group |= group >> 4;
       group |= group >> 8;
       group = (uint16_t)_tableDeBruijn[(uint16_t)(group * 0xf2d) >> 12];

       prio = _readyThreadByPrio[group];
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio |= prio >> 8;
       prio = (uint16_t)_tableDeBruijn[(uint16_t)(prio * 0xf2d) >> 12];

       return (nOS_Thread*)nOS_readyThreadsList[(group << 4) | prio].head->payload;
   }
  #endif
 #else
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 8)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint8_t prio;

       prio = _readyThreadByPrio;
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio = (uint8_t)_tableDeBruijn[(uint8_t)(prio * 0x1d) >> 5];

       return (nOS_Thread*)nOS_readyThreadsList[prio].head->payload;
   }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint16_t    prio;

       prio = _readyThreadByPrio;
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio |= prio >> 8;
       prio = (uint16_t)_tableDeBruijn[(uint16_t)(prio * 0xf2d) >> 12];

       return (nOS_Thread*)nOS_readyThreadsList[prio].head->payload;
   }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 64)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint8_t     group;
       uint8_t     prio;

       group = _readyThreadByGroup;
       group |= group >> 1; // first round down to one less than a power of 2
       group |= group >> 2;
       group |= group >> 4;
       group = (uint8_t)_tableDeBruijn[(uint8_t)(group * 0x1d) >> 5];

       prio = _readyThreadByPrio[group];
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio = (uint8_t)_tableDeBruijn[(uint8_t)(prio * 0x1d) >> 5];

       return (nOS_Thread*)nOS_readyThreadsList[(group << 3) | prio].head->payload;
   }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
   nOS_Thread* nOS_FindHighPrioThread(void)
   {
       uint16_t    group;
       uint16_t    prio;

       group = _readyThreadByGroup;
       group |= group >> 1; // first round down to one less than a power of 2
       group |= group >> 2;
       group |= group >> 4;
       group |= group >> 8;
       group = (uint16_t)_tableDeBruijn[(uint16_t)(group * 0xf2d) >> 12];

       prio = _readyThreadByPrio[group];
       prio |= prio >> 1; // first round down to one less than a power of 2
       prio |= prio >> 2;
       prio |= prio >> 4;
       prio |= prio >> 8;
       prio = (uint16_t)_tableDeBruijn[(uint16_t)(prio * 0xf2d) >> 12];

       return (nOS_Thread*)nOS_readyThreadsList[(group << 4) | prio].head->payload;
   }
  #endif
 #endif

 #ifdef NOS_32_BITS_SCHEDULER
  void nOS_AppendThreadToReadyList (nOS_Thread *thread)
  {
     /* we use 32 bits variables for maximum performance */
      uint32_t    prio = (uint32_t)thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 32)
      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio |= (0x00000001UL << prio);
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint32_t    group = (prio >> 5UL) & 0x00000007UL;

      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio[group] |= (0x00000001UL << (prio & 0x0000001fUL));
      _readyThreadByGroup |= (0x00000001UL << group);
  #endif
  }
  void nOS_RemoveThreadFromReadyList (nOS_Thread *thread)
  {
      /* we use 32 bits variables for maximum performance */
      uint32_t    prio = (uint32_t)thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 32)
      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio &=~ (0x00000001UL << prio);
      }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint32_t    group = (prio >> 5UL) & 0x00000007UL;

      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio[group] &=~ (0x00000001UL << (prio & 0x0000001fUL));
          if (_readyThreadByPrio[group] == 0x00000000UL) {
              _readyThreadByGroup &=~ (0x00000001UL << group);
          }
      }
  #endif
  }
 #elif defined(NOS_16_BITS_SCHEDULER)
  void nOS_AppendThreadToReadyList (nOS_Thread *thread)
  {
      /* we use 16 bits variables for maximum performance */
      uint16_t    prio = (uint16_t)thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio |= (0x0001 << prio);
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint16_t    group = (prio >> 4) & 0x000F;

      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio[group] |= (0x0001 << (prio & 0x0f));
      _readyThreadByGroup |= (0x0001 << group);
  #endif
  }
  void nOS_RemoveThreadFromReadyList (nOS_Thread *thread)
  {
      /* we use 16 bits variables for maximum performance */
      uint16_t    prio = (uint16_t)thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio &=~ (0x0001 << prio);
      }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint16_t    group = (prio >> 4) & 0x000F;

      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio[group] &=~ (0x0001 << (prio & 0x0f));
          if (_readyThreadByPrio[group] == 0x0000) {
              _readyThreadByGroup &=~ (0x0001 << group);
          }
      }
  #endif
  }
 #else   /* NOS_32_BITS_SCHEDULER */
  void nOS_AppendThreadToReadyList (nOS_Thread *thread)
  {
      uint8_t prio = thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 8)
      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio |= (0x01 << prio);
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio |= (0x0001 << prio);
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 64)
      uint8_t     group = (prio >> 3) & 0x07;

      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio[group] |= (0x01 << (prio & 0x07));
      _readyThreadByGroup |= (0x01 << group);
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint8_t     group = (prio >> 4) & 0x0F;

      nOS_AppendToList(&nOS_readyThreadsList[prio], &thread->readyWait);
      _readyThreadByPrio[group] |= (0x0001 << (prio & 0x0f));
      _readyThreadByGroup |= (0x0001 << group);
  #endif
  }
  void nOS_RemoveThreadFromReadyList (nOS_Thread *thread)
  {
      uint8_t prio = thread->prio;

  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO < 8)
      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio &=~ (0x01 << prio);
      }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 16)
      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio &=~ (0x0001 << prio);
      }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 64)
      uint8_t     group = (prio >> 3) & 0x07;

      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio[group] &=~ (0x01 << (prio & 0x07));
          if (_readyThreadByPrio[group] == 0x00) {
              _readyThreadByGroup &=~ (0x01 << group);
          }
      }
  #elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 256)
      uint8_t     group = (prio >> 4) & 0x0F;

      nOS_RemoveFromList(&nOS_readyThreadsList[prio], &thread->readyWait);
      if (nOS_readyThreadsList[prio].head == NULL) {
          _readyThreadByPrio[group] &=~ (0x0001 << (prio & 0x0f));
          if (_readyThreadByPrio[group] == 0x0000) {
              _readyThreadByGroup &=~ (0x0001 << group);
          }
      }
  #endif
  }
 #endif
#endif

nOS_Error nOS_Schedule(void)
{
    nOS_Error   err;

#if (NOS_CONFIG_SAFE > 0)
    /* Switch only if initialization is completed */
    if (!nOS_running) {
        err = NOS_E_NOT_RUNNING;
    } else
#endif
    if (nOS_isrNestingCounter > 0) {
        /* Can't switch context from ISR */
        err = NOS_E_ISR;
    } else
#if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    if (nOS_lockNestingCounter > 0) {
        /* Can't switch context when scheduler is locked */
        err = NOS_E_LOCKED;
    } else
#endif
    {
        /* Recheck if current running thread is the highest prio thread */
        nOS_highPrioThread = nOS_FindHighPrioThread();
        if (nOS_runningThread != nOS_highPrioThread) {
            nOS_SwitchContext();
        }
        err = NOS_OK;
    }

    return err;
}

nOS_Error nOS_Init(void)
{
    nOS_Error   err;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
    uint16_t    i;
#endif

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_initialized) {
        err = NOS_E_INIT;
    } else
#endif
    {
        nOS_tickCounter = 0;
        nOS_isrNestingCounter = 0;
#if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
        nOS_lockNestingCounter = 0;
#endif

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
        for (i = 0; i <= NOS_CONFIG_HIGHEST_THREAD_PRIO; i++) {
            nOS_InitList(&nOS_readyThreadsList[i]);
        }
#else
        nOS_InitList(&nOS_readyThreadsList);
#endif
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
        nOS_InitList(&nOS_timeoutThreadsList);
#endif
#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
        nOS_InitList(&nOS_allThreadsList);
#endif

#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
        nOS_idleHandle.prio = NOS_THREAD_PRIO_IDLE;
#endif
        nOS_idleHandle.state = NOS_THREAD_READY;
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
        nOS_idleHandle.timeout = 0;
#endif
        nOS_idleHandle.readyWait.payload = &nOS_idleHandle;
        nOS_AppendThreadToReadyList(&nOS_idleHandle);
        nOS_runningThread = &nOS_idleHandle;
        nOS_highPrioThread = &nOS_idleHandle;

        /* Let port doing special initialization if needed */
        nOS_InitSpecific();

#if (NOS_CONFIG_TIMER_ENABLE > 0)
        nOS_InitTimer();
#endif
#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
        nOS_InitSignal();
#endif
#if (NOS_CONFIG_TIME_ENABLE > 0)
        nOS_InitTime();
#endif
#if (NOS_CONFIG_ALARM_ENABLE > 0)
        nOS_InitAlarm();
#endif

        nOS_initialized = true;

        err = NOS_OK;
    }

    return err;
}

nOS_Error nOS_Start(void)
{
    nOS_Error       err;
#if (NOS_CONFIG_SAFE > 0)
    nOS_StatusReg   sr;

    if (!nOS_initialized) {
        nOS_EnterCritical(sr);
        nOS_Init();
        nOS_LeaveCritical(sr);
    }

    if (nOS_running) {
        err = NOS_E_RUNNING;
    } else
#endif
    {
        /* Context switching is possible after this point */
        nOS_running = true;

        err = NOS_OK;
    }

    return err;
}

nOS_Error nOS_Yield(void)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    if (nOS_lockNestingCounter > 0) {
        err = NOS_E_LOCKED;
    } else
 #endif
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
        nOS_RotateList(&nOS_readyThreadsList[nOS_runningThread->prio]);
#else
        nOS_RotateList(&nOS_readyThreadsList);
#endif
        err = nOS_Schedule();
        nOS_LeaveCritical(sr);
    }

    return err;
}

void nOS_Tick(nOS_TickCounter ticks)
{
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (ticks > 0)
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
        nOS_WalkInList(&nOS_timeoutThreadsList, nOS_TickThread, &ticks);
#endif
#if (NOS_CONFIG_TIMER_ENABLE > 0) && (NOS_CONFIG_TIMER_TICK_ENABLE > 0)
        nOS_TimerTick(ticks);
#endif
#if (NOS_CONFIG_TIME_ENABLE > 0) && (NOS_CONFIG_TIME_TICK_ENABLE > 0)
        nOS_TimeTick(ticks);
#endif
#if (NOS_CONFIG_ALARM_ENABLE > 0) && (NOS_CONFIG_ALARM_TICK_ENABLE > 0)
        nOS_AlarmTick();
#endif
#if (NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE > 0)
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
        nOS_RotateList(&nOS_readyThreadsList[nOS_runningThread->prio]);
 #else
        nOS_RotateList(&nOS_readyThreadsList);
 #endif
#endif
        nOS_tickCounter += ticks;
        nOS_LeaveCritical(sr);
    }
}

nOS_TickCounter nOS_GetTickCount(void)
{
    nOS_StatusReg   sr;
    nOS_TickCounter tickcnt;

    nOS_EnterCritical(sr);
    tickcnt = nOS_tickCounter;
    nOS_LeaveCritical(sr);

    return tickcnt;
}

#if defined(NOS_CONFIG_TICKS_PER_SECOND) && (NOS_CONFIG_TICKS_PER_SECOND > 0)
uint32_t nOS_MsToTicks (uint16_t ms)
{
    uint32_t    ticks;

    /* Convert ms to ticks: ms/1000 = ticks/NOS_CONFIG_TICKS_PER_SECOND */
    ticks = (uint32_t)ms * NOS_CONFIG_TICKS_PER_SECOND;
    /* Round to upper tick count */
    if ((ticks % 1000) > 0) {
        ticks += 1000;
    }
    ticks /= 1000;

    return ticks;
}
#endif

#if (NOS_CONFIG_SLEEP_ENABLE > 0)
nOS_Error nOS_Sleep (nOS_TickCounter ticks)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    /* Can't switch context when scheduler is locked */
    if (nOS_lockNestingCounter > 0) {
        err = NOS_E_LOCKED;
    } else
 #endif
    if (nOS_runningThread == &nOS_idleHandle) {
        err = NOS_E_IDLE;
    } else
#endif
    if (ticks == 0) {
        err = nOS_Yield();
    }
    else {
        nOS_EnterCritical(sr);
        err = nOS_WaitForEvent(NULL, NOS_THREAD_SLEEPING, ticks);
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if defined(NOS_CONFIG_TICKS_PER_SECOND) && (NOS_CONFIG_TICKS_PER_SECOND > 0)
nOS_Error nOS_SleepMs (uint16_t ms)
{
    nOS_Error       err;
    nOS_StatusReg   sr;
    uint32_t        ticks;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    /* Can't switch context when scheduler is locked */
    if (nOS_lockNestingCounter > 0) {
        err = NOS_E_LOCKED;
    } else
 #endif
    if (nOS_runningThread == &nOS_idleHandle) {
        err = NOS_E_IDLE;
    } else
#endif
    if (ms == 0) {
        err = nOS_Yield();
    }
    else {
        ticks = nOS_MsToTicks(ms);

        nOS_EnterCritical(sr);
        err = NOS_OK;
        while ((err == NOS_OK) && (ticks > NOS_TICKS_WAIT_MAX)) {
            err = nOS_WaitForEvent(NULL, NOS_THREAD_SLEEPING, NOS_TICKS_WAIT_MAX);
            ticks -= NOS_TICKS_WAIT_MAX;
        }
        if ((err == NOS_OK) && (ticks > 0)) {
            err = nOS_WaitForEvent(NULL, NOS_THREAD_SLEEPING, ticks);
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_TICKS_PER_SECOND & NOS_CONFIG_TICKS_PER_SECOND */
#endif  /* NOS_CONFIG_SLEEP_ENABLE */

#if (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
nOS_Error nOS_SleepUntil (nOS_TickCounter tick)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    /* Can't switch context when scheduler is locked */
    if (nOS_lockNestingCounter > 0) {
        err = NOS_E_LOCKED;
    } else
 #endif
    if (nOS_runningThread == &nOS_idleHandle) {
        err = NOS_E_IDLE;
    } else
#endif
    {
        nOS_EnterCritical(sr);
        err = NOS_OK;
        if (tick != nOS_tickCounter) {
            /* Always give number of ticks to wait to this function */
            err = nOS_WaitForEvent(NULL, NOS_THREAD_SLEEPING, tick - nOS_tickCounter);
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_SLEEP_UNTIL_ENABLE */

#if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
nOS_Error nOS_SchedLock(void)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (nOS_lockNestingCounter == UINT8_MAX) {
            err = NOS_E_OVERFLOW;
        } else
#endif
        {
            nOS_lockNestingCounter++;
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

nOS_Error nOS_SchedUnlock(void)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (nOS_lockNestingCounter == 0) {
            err = NOS_E_UNDERFLOW;
        } else
#endif
        {
            nOS_lockNestingCounter--;
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
            if (nOS_lockNestingCounter == 0) {
                /* Verify if a highest prio thread is ready to run */
                nOS_Schedule();
            }
#endif
            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_SCHED_LOCK_ENABLE */

nOS_Thread * nOS_GetRunningThread (void)
{
    nOS_Thread *thread;

#if (NOS_CONFIG_SAFE > 0)
    if (!nOS_running) {
        thread = NULL;
    } else
#endif
    {
        thread = nOS_runningThread;
    }

    return thread;
}

#ifdef __cplusplus
}
#endif
