/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#ifndef NOS_H
#define NOS_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdlib.h>
#include <string.h>

#define _C99_COMPLIANT_         0
#ifdef __STDC__
 #ifdef __STDC_VERSION__
  #if (__STDC_VERSION__ >= 199901L)
   #undef  _C99_COMPLIANT_
   #define _C99_COMPLIANT_      1
  #endif
 #endif
#endif
#ifdef ARDUINO
 #define _C99_COMPLIANT_        1
#endif

#if (_C99_COMPLIANT_ > 0) || defined(__cplusplus)
 #include <stdint.h>
 #ifndef __cplusplus
  #include <stdbool.h>
 #endif
#else
 #ifdef WIN32
  #define bool              BOOLEAN
 #else
  #define bool              _Bool
 #endif
 #define false              0
 #define true               1
 typedef signed char        int8_t;
 typedef unsigned char      uint8_t;
 typedef signed short       int16_t;
 typedef unsigned short     uint16_t;
 typedef signed long        int32_t;
 typedef unsigned long      uint32_t;
 typedef signed long long   int64_t;
 typedef unsigned long long uint64_t;
#endif

#ifndef UINT8_MAX
#define UINT8_MAX                   255U
#endif

#ifndef UINT16_MAX
#define UINT16_MAX                  65535U
#endif

#ifndef UINT32_MAX
#define UINT32_MAX                  4294967295UL
#endif

#ifndef UINT64_MAX
#define UINT64_MAX                  18446744073709551615ULL
#endif

#define NOS_QUOTE(s)                #s
#define NOS_STR(s)                  NOS_QUOTE(s)
#define NOS_VERSION                 NOS_STR(NOS_VERSION_MAJOR)"."NOS_STR(NOS_VERSION_MINOR)"."NOS_STR(NOS_VERSION_BUILD)

#define NOS_VERSION_MAJOR           0
#define NOS_VERSION_MINOR           1
#define NOS_VERSION_BUILD           0

#ifdef NOS_GLOBALS
 #define NOS_EXTERN
#else
 #define NOS_EXTERN                 extern
#endif

#include "nOSConfig.h"

#ifndef NOS_CONFIG_DEBUG
 #error "nOSConfig.h: NOS_CONFIG_DEBUG is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_DEBUG != 0) && (NOS_CONFIG_DEBUG != 1)
 #error "nOSConfig.h: NOS_CONFIG_DEBUG is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_SAFE
 #error "nOSConfig.h: NOS_CONFIG_SAFE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SAFE != 0) && (NOS_CONFIG_SAFE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SAFE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_HIGHEST_THREAD_PRIO
 #error "nOSConfig.h: NOS_CONFIG_HIGHEST_THREAD_PRIO is not defined: must be set between 0 and 255 inclusively."
#elif (NOS_CONFIG_HIGHEST_THREAD_PRIO < 0) || (NOS_CONFIG_HIGHEST_THREAD_PRIO > 255)
 #error "nOSConfig.h: NOS_CONFIG_HIGHEST_THREAD_PRIO is set to invalid value: must be set between 0 and 255 inclusively."
#endif

#ifndef NOS_CONFIG_TICK_COUNT_WIDTH
 #error "nOSConfig.h: NOS_CONFIG_TICK_COUNT_WIDTH is not defined: must be set to 8, 16, 32 or 64."
#elif (NOS_CONFIG_TICK_COUNT_WIDTH != 8) && (NOS_CONFIG_TICK_COUNT_WIDTH != 16) && (NOS_CONFIG_TICK_COUNT_WIDTH != 32) && (NOS_CONFIG_TICK_COUNT_WIDTH != 64)
 #error "nOSConfig.h: NOS_CONFIG_TICK_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
#endif

#ifndef NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
  #error "nOSConfig.h: NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE is not defined: must be set to 0 or 1."
 #endif
#elif (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE != 0) && (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0) && (NOS_CONFIG_HIGHEST_THREAD_PRIO == 0)
 #error "nOSConfig.h: NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE can't be use when NOS_CONFIG_HIGHEST_THREAD_PRIO == 0 (cooperative scheduling)."
#endif

#ifndef NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE != 0) && (NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE > 0) && (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE == 0) && (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
 #error "nOSConfig.h: NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE should not be used in cooperative scheduling with more than 1 level of priority."
#endif

#ifndef NOS_CONFIG_SCHED_LOCK_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SCHED_LOCK_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SCHED_LOCK_ENABLE != 0) && (NOS_CONFIG_SCHED_LOCK_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SCHED_LOCK_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_SLEEP_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SLEEP_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SLEEP_ENABLE != 0) && (NOS_CONFIG_SLEEP_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SLEEP_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_SLEEP_UNTIL_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SLEEP_UNTIL_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SLEEP_UNTIL_ENABLE != 0) && (NOS_CONFIG_SLEEP_UNTIL_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SLEEP_UNTIL_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_THREAD_SUSPEND_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_SUSPEND_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_SUSPEND_ENABLE != 0) && (NOS_CONFIG_THREAD_SUSPEND_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_SUSPEND_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
 #ifndef NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE != 0) && (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
#else
 #undef NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE
 #define NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE   0
#endif

#ifndef NOS_CONFIG_THREAD_DELETE_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_DELETE_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_DELETE_ENABLE != 0) && (NOS_CONFIG_THREAD_DELETE_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_THREAD_ABORT_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_ABORT_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_ABORT_ENABLE != 0) && (NOS_CONFIG_THREAD_ABORT_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_ABORT_ENABLE is not defined: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_THREAD_SET_PRIO_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_SET_PRIO_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_SET_PRIO_ENABLE != 0) && (NOS_CONFIG_THREAD_SET_PRIO_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_SET_PRIO_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_THREAD_NAME_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_NAME_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_NAME_ENABLE != 0) && (NOS_CONFIG_THREAD_NAME_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_NAME_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_THREAD_JOIN_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_THREAD_JOIN_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_THREAD_JOIN_ENABLE != 0) && (NOS_CONFIG_THREAD_JOIN_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_THREAD_JOIN_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_WAITING_TIMEOUT_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_WAITING_TIMEOUT_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_WAITING_TIMEOUT_ENABLE != 0) && (NOS_CONFIG_WAITING_TIMEOUT_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_WAITING_TIMEOUT_ENABLE is set to invalid value: must be set to 0 or 1."
#endif

#ifndef NOS_CONFIG_SEM_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SEM_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SEM_ENABLE != 0) && (NOS_CONFIG_SEM_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SEM_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_SEM_ENABLE > 0)
 #ifndef NOS_CONFIG_SEM_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_SEM_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_SEM_DELETE_ENABLE != 0) && (NOS_CONFIG_SEM_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_SEM_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_SEM_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_SEM_COUNT_WIDTH is not defined: must be set to 8, 16, 32, or 64."
 #elif (NOS_CONFIG_SEM_COUNT_WIDTH != 8) && (NOS_CONFIG_SEM_COUNT_WIDTH != 16) && (NOS_CONFIG_SEM_COUNT_WIDTH != 32) && (NOS_CONFIG_SEM_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_SEM_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_SEM_DELETE_ENABLE
 #undef NOS_CONFIG_SEM_COUNT_WIDTH
#endif

#ifndef NOS_CONFIG_MUTEX_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_MUTEX_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_MUTEX_ENABLE != 0) && (NOS_CONFIG_MUTEX_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_MUTEX_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_MUTEX_ENABLE > 0)
 #ifndef NOS_CONFIG_MUTEX_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_MUTEX_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_MUTEX_DELETE_ENABLE != 0) && (NOS_CONFIG_MUTEX_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_MUTEX_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_MUTEX_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_MUTEX_COUNT_WIDTH is not defined: must be set to 8, 16, 32, or 64."
 #elif (NOS_CONFIG_MUTEX_COUNT_WIDTH != 8) && (NOS_CONFIG_MUTEX_COUNT_WIDTH != 16) && (NOS_CONFIG_MUTEX_COUNT_WIDTH != 32) && (NOS_CONFIG_MUTEX_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_MUTEX_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_MUTEX_DELETE_ENABLE
 #undef NOS_CONFIG_MUTEX_COUNT_WIDTH
#endif

#ifndef NOS_CONFIG_FLAG_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_FLAG_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_FLAG_ENABLE != 0) && (NOS_CONFIG_FLAG_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_FLAG_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_FLAG_ENABLE > 0)
 #ifndef NOS_CONFIG_FLAG_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_FLAG_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_FLAG_DELETE_ENABLE != 0) && (NOS_CONFIG_FLAG_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_FLAG_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_FLAG_NB_BITS
  #error "nOSConfig.h: NOS_CONFIG_FLAG_NB_BITS is not defined: must be set to 8, 16, 32 or 64."
 #elif (NOS_CONFIG_FLAG_NB_BITS != 8) && (NOS_CONFIG_FLAG_NB_BITS != 16) && (NOS_CONFIG_FLAG_NB_BITS != 32) && (NOS_CONFIG_FLAG_NB_BITS != 64)
  #error "nOSConfig.h: NOS_CONFIG_FLAG_NB_BITS is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_FLAG_DELETE_ENABLE
 #undef NOS_CONFIG_FLAG_NB_BITS
#endif

#ifndef NOS_CONFIG_QUEUE_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_QUEUE_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_QUEUE_ENABLE != 0) && (NOS_CONFIG_QUEUE_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_QUEUE_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_QUEUE_ENABLE > 0)
 #ifndef NOS_CONFIG_QUEUE_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_QUEUE_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_QUEUE_DELETE_ENABLE != 0) && (NOS_CONFIG_QUEUE_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_QUEUE_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH is not defined: must be set to 8, 16, 32, or 64."
 #elif (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH != 8) && (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH != 16) && (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH != 32) && (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_QUEUE_DELETE_ENABLE
 #undef NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH
#endif

#ifndef NOS_CONFIG_MEM_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_MEM_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_MEM_ENABLE != 0) && (NOS_CONFIG_MEM_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_MEM_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_MEM_ENABLE > 0)
 #ifndef NOS_CONFIG_MEM_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_MEM_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_MEM_DELETE_ENABLE != 0) && (NOS_CONFIG_MEM_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_MEM_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
  #ifndef NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH is not defined: must be set to 8, 16, 32, or 64."
 #elif (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH != 8) && (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH != 16) && (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH != 32) && (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
  #ifndef NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH is not defined: must be set to 8, 16, 32, or 64."
 #elif (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH != 8) && (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH != 16) && (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH != 32) && (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
 #ifndef NOS_CONFIG_MEM_SANITY_CHECK_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_MEM_SANITY_CHECK_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE != 0) && (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_MEM_SANITY_CHECK_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
#else
 #undef NOS_CONFIG_MEM_DELETE_ENABLE
 #undef NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH
 #undef NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH
 #undef NOS_CONFIG_MEM_SANITY_CHECK_ENABLE
#endif

#ifndef NOS_CONFIG_TIMER_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_TIMER_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_TIMER_ENABLE != 0) && (NOS_CONFIG_TIMER_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_TIMER_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_TIMER_ENABLE > 0)
 #ifndef NOS_CONFIG_TIMER_TICK_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_TIMER_TICK_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIMER_TICK_ENABLE != 0) && (NOS_CONFIG_TIMER_TICK_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_TIMER_TICK_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_TIMER_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_TIMER_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIMER_DELETE_ENABLE != 0) && (NOS_CONFIG_TIMER_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_TIMER_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_TIMER_HIGHEST_PRIO
  #error "nOSConfig.h: NOS_CONFIG_TIMER_HIGHEST_PRIO is not defined: must be set between 0 and 7 inclusively."
 #elif (NOS_CONFIG_TIMER_HIGHEST_PRIO < 0) || (NOS_CONFIG_TIMER_HIGHEST_PRIO > 7)
  #error "nOSConfig.h: NOS_CONFIG_TIMER_HIGHEST_PRIO is set to invalid value: must be set between 0 and 7 inclusively."
 #endif
 #ifndef NOS_CONFIG_TIMER_THREAD_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIMER_THREAD_ENABLE != 0) && (NOS_CONFIG_TIMER_THREAD_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_ENABLE is set to invalid value: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
   #ifndef NOS_CONFIG_TIMER_THREAD_PRIO
    #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_PRIO is not defined: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_TIMER_THREAD_PRIO < 0)
    #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_PRIO is set to invalid value: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_TIMER_THREAD_PRIO > NOS_CONFIG_HIGHEST_THREAD_PRIO)
    #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_PRIO is higher than NOS_CONFIG_HIGHEST_THREAD_PRIO: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #endif
  #else
   #undef NOS_CONFIG_TIMER_THREAD_PRIO
  #endif
  #ifndef NOS_CONFIG_TIMER_THREAD_STACK_SIZE
   #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_STACK_SIZE is not defined."
  #endif
 #else
  #undef NOS_CONFIG_TIMER_THREAD_PRIO
  #undef NOS_CONFIG_TIMER_THREAD_STACK_SIZE
 #endif
 #ifndef NOS_CONFIG_TIMER_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_TIMER_COUNT_WIDTH is not defined: must be set to 8, 16, 32 or 64."
 #elif (NOS_CONFIG_TIMER_COUNT_WIDTH != 8) && (NOS_CONFIG_TIMER_COUNT_WIDTH != 16) && (NOS_CONFIG_TIMER_COUNT_WIDTH != 32) && (NOS_CONFIG_TIMER_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_TIMER_COUNT_WIDTH is set to invalid value: must be set to 8, 16, 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_TIMER_TICK_ENABLE
 #undef NOS_CONFIG_TIMER_DELETE_ENABLE
 #undef NOS_CONFIG_TIMER_HIGHEST_PRIO
 #undef NOS_CONFIG_TIMER_THREAD_ENABLE
 #undef NOS_CONFIG_TIMER_THREAD_PRIO
 #undef NOS_CONFIG_TIMER_THREAD_STACK_SIZE
 #undef NOS_CONFIG_TIMER_COUNT_WIDTH
#endif

#ifndef NOS_CONFIG_SIGNAL_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_SIGNAL_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_SIGNAL_ENABLE != 0) && (NOS_CONFIG_SIGNAL_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_SIGNAL_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_SIGNAL_ENABLE > 0)
 #ifndef NOS_CONFIG_SIGNAL_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_SIGNAL_DELETE_ENABLE != 0) && (NOS_CONFIG_SIGNAL_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_SIGNAL_HIGHEST_PRIO
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_HIGHEST_PRIO is not defined: must be set between 0 and 7 inclusively."
 #elif (NOS_CONFIG_SIGNAL_HIGHEST_PRIO < 0) || (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 7)
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_HIGHEST_PRIO is set to invalid value: must be set between 0 and 7 inclusively."
 #endif
 #ifndef NOS_CONFIG_SIGNAL_THREAD_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_SIGNAL_THREAD_ENABLE != 0) && (NOS_CONFIG_SIGNAL_THREAD_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_ENABLE is set to invalid value: must be set to 0 or 1."
 #elif (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
   #ifndef NOS_CONFIG_SIGNAL_THREAD_PRIO
    #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_PRIO is not defined: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_SIGNAL_THREAD_PRIO < 0)
    #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_PRIO is set to invalid value: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_SIGNAL_THREAD_PRIO > NOS_CONFIG_HIGHEST_THREAD_PRIO)
    #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_PRIO is higher than NOS_CONFIG_HIGHEST_THREAD_PRIO: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #endif
  #else
   #undef NOS_CONFIG_SIGNAL_THREAD_PRIO
  #endif
  #ifndef NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE
   #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE is not defined."
  #endif
 #else
  #undef NOS_CONFIG_SIGNAL_THREAD_PRIO
  #undef NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE
 #endif
#else
 #undef NOS_CONFIG_SIGNAL_DELETE_ENABLE
 #undef NOS_CONFIG_SIGNAL_HIGHEST_PRIO
 #undef NOS_CONFIG_SIGNAL_THREAD_ENABLE
 #undef NOS_CONFIG_SIGNAL_THREAD_PRIO
 #undef NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE
#endif

#ifndef NOS_CONFIG_TIME_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_TIME_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_TIME_ENABLE != 0) && (NOS_CONFIG_TIME_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_TIME_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_TIME_ENABLE > 0)
 #ifndef NOS_CONFIG_TIME_TICK_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_TIME_TICK_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIME_TICK_ENABLE != 0) && (NOS_CONFIG_TIME_TICK_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_TIME_TICK_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_TIME_WAIT_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_TIME_WAIT_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_TIME_WAIT_ENABLE != 0) && (NOS_CONFIG_TIME_WAIT_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_TIME_WAIT_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_TIME_TICKS_PER_SECOND
  #error "nOSConfig.h: NOS_CONFIG_TIME_TICKS_PER_SECOND is not defined: must be higher than 0."
 #elif (NOS_CONFIG_TIME_TICKS_PER_SECOND == 0)
  #error "nOSConfig.h: NOS_CONFIG_TIME_TICKS_PER_SECOND is set to invalue value: must be higher than 0."
 #elif defined(NOS_CONFIG_TICKS_PER_SECOND) && (NOS_CONFIG_TICKS_PER_SECOND > 0)
  #if (NOS_CONFIG_TIME_TICK_ENABLE > 0) && (NOS_CONFIG_TIME_TICKS_PER_SECOND != NOS_CONFIG_TICKS_PER_SECOND)
   #error "nOSConfig.h: NOS_CONFIG_TIME_TICKS_PER_SECOND is not equal to NOS_CONFIG_TICKS_PER_SECOND: must be equal when NOS_CONFIG_TIME_TICK_ENABLE is enabled."
  #endif
 #endif
 #ifndef NOS_CONFIG_TIME_COUNT_WIDTH
  #error "nOSConfig.h: NOS_CONFIG_TIME_COUNT_WIDTH is not defined: must be set to 32 or 64."
 #elif (NOS_CONFIG_TIME_COUNT_WIDTH != 32) && (NOS_CONFIG_TIME_COUNT_WIDTH != 64)
  #error "nOSConfig.h: NOS_CONFIG_TIME_COUNT_WIDTH is set to invalid value: must be set to 32 or 64."
 #endif
#else
 #undef NOS_CONFIG_TIME_TICK_ENABLE
 #undef NOS_CONFIG_TIME_WAIT_ENABLE
 #undef NOS_CONFIG_TIME_TICKS_PER_SECOND
 #undef NOS_CONFIG_TIME_COUNT_WIDTH
#endif

#ifndef NOS_CONFIG_ALARM_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_ALARM_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_ALARM_ENABLE != 0) && (NOS_CONFIG_ALARM_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_ALARM_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_ALARM_ENABLE > 0)
 #if (NOS_CONFIG_TIME_ENABLE == 0)
  #error "nOSConfig.h: Time module is not enabled: Alarm module is dependant from Time module."
 #endif
 #ifndef NOS_CONFIG_ALARM_TICK_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_ALARM_TICK_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_ALARM_TICK_ENABLE != 0) && (NOS_CONFIG_ALARM_TICK_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_ALARM_TICK_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_ALARM_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_ALARM_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_ALARM_DELETE_ENABLE != 0) && (NOS_CONFIG_ALARM_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_ALARM_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
 #ifndef NOS_CONFIG_ALARM_THREAD_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_ALARM_THREAD_ENABLE != 0) && (NOS_CONFIG_ALARM_THREAD_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_ENABLE is set to invalid value: must be set to 0 or 1."
 #elif (NOS_CONFIG_ALARM_THREAD_ENABLE > 0)
  #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
   #ifndef NOS_CONFIG_ALARM_THREAD_PRIO
    #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_PRIO is not defined: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_ALARM_THREAD_PRIO < 0)
    #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_PRIO is set to invalid value: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #elif (NOS_CONFIG_ALARM_THREAD_PRIO > NOS_CONFIG_HIGHEST_THREAD_PRIO)
    #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_PRIO is higher than NOS_CONFIG_HIGHEST_THREAD_PRIO: must be set between 0 and NOS_CONFIG_HIGHEST_THREAD_PRIO inclusively."
   #endif
  #else
   #undef NOS_CONFIG_ALARM_THREAD_PRIO
  #endif
  #ifndef NOS_CONFIG_ALARM_THREAD_STACK_SIZE
   #error "nOSConfig.h: NOS_CONFIG_ALARM_THREAD_STACK_SIZE is not defined."
  #endif
 #else
  #undef NOS_CONFIG_ALARM_THREAD_PRIO
  #undef NOS_CONFIG_ALARM_THREAD_STACK_SIZE
 #endif
#else
 #undef NOS_CONFIG_ALARM_TICK_ENABLE
 #undef NOS_CONFIG_ALARM_DELETE_ENABLE
 #undef NOS_CONFIG_ALARM_THREAD_ENABLE
 #undef NOS_CONFIG_ALARM_THREAD_PRIO
 #undef NOS_CONFIG_ALARM_THREAD_STACK_SIZE
#endif

#ifndef NOS_CONFIG_BARRIER_ENABLE
 #error "nOSConfig.h: NOS_CONFIG_BARRIER_ENABLE is not defined: must be set to 0 or 1."
#elif (NOS_CONFIG_BARRIER_ENABLE != 0) && (NOS_CONFIG_BARRIER_ENABLE != 1)
 #error "nOSConfig.h: NOS_CONFIG_BARRIER_ENABLE is set to invalid value: must be set to 0 or 1."
#elif (NOS_CONFIG_BARRIER_ENABLE > 0)
 #ifndef NOS_CONFIG_BARRIER_DELETE_ENABLE
  #error "nOSConfig.h: NOS_CONFIG_BARRIER_DELETE_ENABLE is not defined: must be set to 0 or 1."
 #elif (NOS_CONFIG_BARRIER_DELETE_ENABLE != 0) && (NOS_CONFIG_BARRIER_DELETE_ENABLE != 1)
  #error "nOSConfig.h: NOS_CONFIG_BARRIER_DELETE_ENABLE is set to invalid value: must be set to 0 or 1."
 #endif
#else
 #undef NOS_CONFIG_BARRIER_DELETE_ENABLE
#endif

typedef void(*nOS_Callback)(void);
typedef struct nOS_List             nOS_List;
typedef struct nOS_Node             nOS_Node;
typedef void(*nOS_NodeHandler)(void*,void*);
typedef struct nOS_Thread           nOS_Thread;
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
 typedef int(*nOS_ThreadEntry)(void*);
#else
 typedef void(*nOS_ThreadEntry)(void*);
#endif
typedef struct nOS_Event            nOS_Event;
#if (NOS_CONFIG_TICK_COUNT_WIDTH == 8)
 typedef uint8_t                    nOS_TickCounter;
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 16)
 typedef uint16_t                   nOS_TickCounter;
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 32)
 typedef uint32_t                   nOS_TickCounter;
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 64)
 typedef uint64_t                   nOS_TickCounter;
#endif
#if (NOS_CONFIG_SEM_ENABLE > 0)
 typedef struct nOS_Sem             nOS_Sem;
 #if (NOS_CONFIG_SEM_COUNT_WIDTH == 8)
  typedef uint8_t                   nOS_SemCounter;
 #elif (NOS_CONFIG_SEM_COUNT_WIDTH == 16)
  typedef uint16_t                  nOS_SemCounter;
 #elif (NOS_CONFIG_SEM_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_SemCounter;
 #elif (NOS_CONFIG_SEM_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_SemCounter;
 #endif
#endif
#if (NOS_CONFIG_MUTEX_ENABLE > 0)
 typedef struct nOS_Mutex           nOS_Mutex;
 #if (NOS_CONFIG_MUTEX_COUNT_WIDTH == 8)
  typedef uint8_t                   nOS_MutexCounter;
 #elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 16)
  typedef uint16_t                  nOS_MutexCounter;
 #elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_MutexCounter;
 #elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_MutexCounter;
 #endif
#endif
#if (NOS_CONFIG_QUEUE_ENABLE > 0)
 typedef struct nOS_Queue           nOS_Queue;
 #if (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH == 8)
  typedef uint8_t                   nOS_QueueCounter;
 #elif (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH == 16)
  typedef uint16_t                  nOS_QueueCounter;
 #elif (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_QueueCounter;
 #elif (NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_QueueCounter;
 #endif
 typedef void(*nOS_QueueCallback)(nOS_Queue*,void*);
#endif
#if (NOS_CONFIG_FLAG_ENABLE > 0)
 typedef struct nOS_Flag            nOS_Flag;
 typedef struct nOS_FlagContext     nOS_FlagContext;
 #if (NOS_CONFIG_FLAG_NB_BITS == 8)
  typedef uint8_t                   nOS_FlagBits;
 #elif (NOS_CONFIG_FLAG_NB_BITS == 16)
  typedef uint16_t                  nOS_FlagBits;
 #elif (NOS_CONFIG_FLAG_NB_BITS == 32)
  typedef uint32_t                  nOS_FlagBits;
 #elif (NOS_CONFIG_FLAG_NB_BITS == 64)
  typedef uint64_t                  nOS_FlagBits;
 #endif
#endif
#if (NOS_CONFIG_MEM_ENABLE > 0)
 typedef struct nOS_Mem             nOS_Mem;
 #if (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH == 8)
  typedef uint8_t                   nOS_MemSize;
 #elif (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH == 16)
  typedef uint16_t                  nOS_MemSize;
 #elif (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH == 32)
  typedef uint32_t                  nOS_MemSize;
 #elif (NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH == 64)
  typedef uint64_t                  nOS_MemSize;
 #endif
 #if (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH == 8)
  typedef uint8_t                   nOS_MemCounter;
 #elif (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH == 16)
  typedef uint16_t                  nOS_MemCounter;
 #elif (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_MemCounter;
 #elif (NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_MemCounter;
 #endif
#endif
#if (NOS_CONFIG_TIMER_ENABLE > 0)
 typedef struct nOS_Timer           nOS_Timer;
 #if (NOS_CONFIG_TIMER_COUNT_WIDTH == 8)
  typedef uint8_t                   nOS_TimerCounter;
 #elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 16)
  typedef uint16_t                  nOS_TimerCounter;
 #elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_TimerCounter;
 #elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_TimerCounter;
 #endif
 typedef void(*nOS_TimerCallback)(nOS_Timer*,void*);
#endif
#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
 typedef struct nOS_Signal          nOS_Signal;
 typedef void(*nOS_SignalCallback)(nOS_Signal*,void*);
#endif
#if (NOS_CONFIG_TIME_ENABLE > 0)
 #if (NOS_CONFIG_TIME_COUNT_WIDTH == 32)
  typedef uint32_t                  nOS_Time;
 #elif (NOS_CONFIG_TIME_COUNT_WIDTH == 64)
  typedef uint64_t                  nOS_Time;
 #endif
 typedef struct nOS_TimeDate        nOS_TimeDate;
#endif
#if (NOS_CONFIG_ALARM_ENABLE > 0)
 typedef struct nOS_Alarm           nOS_Alarm;
 typedef void(*nOS_AlarmCallback)(nOS_Alarm*,void*);
#endif
#if (NOS_CONFIG_BARRIER_ENABLE > 0)
 typedef struct nOS_Barrier         nOS_Barrier;
#endif

typedef enum nOS_Error
{
    NOS_OK                      = 0,
    NOS_E_NULL                  = -1,
    NOS_E_INV_VAL               = -2,
    NOS_E_LOCKED                = -3,
    NOS_E_ISR                   = -4,
    NOS_E_IDLE                  = -5,
    NOS_E_TIMEOUT               = -6,
    NOS_E_UNDERFLOW             = -7,
    NOS_E_OVERFLOW              = -8,
    NOS_E_AGAIN                 = -9,
    NOS_E_OWNER                 = -10,
    NOS_E_EMPTY                 = -11,
    NOS_E_FULL                  = -12,
    NOS_E_INIT                  = -13,
    NOS_E_DELETED               = -14,
    NOS_E_INV_OBJ               = -15,
    NOS_E_ELAPSED               = -16,
    NOS_E_NOT_CREATED           = -17,
    NOS_E_INV_STATE             = -18,
    NOS_E_NO_CONSUMER           = -19,
    NOS_E_INV_PRIO              = -20,
    NOS_E_ABORT                 = -21,
    NOS_E_RUNNING               = -22,
    NOS_E_NOT_RUNNING           = -23,
    NOS_E_FLUSHED               = -24
} nOS_Error;

typedef enum nOS_ThreadState
{
    NOS_THREAD_STOPPED          = 0x00,
    NOS_THREAD_TAKING_SEM       = 0x01,
    NOS_THREAD_LOCKING_MUTEX    = 0x02,
    NOS_THREAD_READING_QUEUE    = 0x03,
    NOS_THREAD_WRITING_QUEUE    = 0x04,
    NOS_THREAD_WAITING_FLAG     = 0x05,
    NOS_THREAD_ALLOC_MEM        = 0x06,
    NOS_THREAD_SLEEPING         = 0x07,
    NOS_THREAD_WAITING_TIME     = 0x08,
    NOS_THREAD_ON_BARRIER       = 0x09,
    NOS_THREAD_JOINING          = 0x0A,
    NOS_THREAD_ON_HOLD          = 0x0F,
    NOS_THREAD_WAITING_MASK     = 0x0F,
    NOS_THREAD_FINISHED         = 0x10,
    NOS_THREAD_WAIT_TIMEOUT     = 0x20,
    NOS_THREAD_SUSPENDED        = 0x40,
    NOS_THREAD_READY            = 0x80
} nOS_ThreadState;

#if (NOS_CONFIG_SAFE > 0)
typedef enum nOS_EventType
{
    NOS_EVENT_INVALID           = 0x00,
    NOS_EVENT_BASE              = 0x01,
    NOS_EVENT_SEM               = 0x02,
    NOS_EVENT_MUTEX             = 0x03,
    NOS_EVENT_QUEUE             = 0x04,
    NOS_EVENT_FLAG              = 0x05,
    NOS_EVENT_MEM               = 0x06,
    NOS_EVENT_BARRIER           = 0x07
} nOS_EventType;
#endif

#if (NOS_CONFIG_MUTEX_ENABLE > 0)
typedef enum nOS_MutexType
{
    NOS_MUTEX_NORMAL            = 0x00,
    NOS_MUTEX_RECURSIVE         = 0x01
} nOS_MutexType;
#endif

#if (NOS_CONFIG_FLAG_ENABLE > 0)
typedef enum nOS_FlagOption
{
    NOS_FLAG_WAIT_ANY           = 0x00,
    NOS_FLAG_WAIT_ALL           = 0x01,
    NOS_FLAG_WAIT               = 0x01,
    NOS_FLAG_CLEAR_ON_EXIT      = 0x02
} nOS_FlagOption;
#endif

#if (NOS_CONFIG_TIMER_ENABLE > 0)
typedef enum nOS_TimerMode
{
    NOS_TIMER_ONE_SHOT          = 0x00,
    NOS_TIMER_FREE_RUNNING      = 0x01,
    NOS_TIMER_MODE              = 0x01
} nOS_TimerMode;

typedef enum nOS_TimerState
{
    NOS_TIMER_DELETED           = 0x00,
    NOS_TIMER_PAUSED            = 0x20,
    NOS_TIMER_RUNNING           = 0x40,
    NOS_TIMER_CREATED           = 0x80
} nOS_TimerState;
#endif

#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
typedef enum nOS_SignalState
{
    NOS_SIGNAL_DELETED          = 0x00,
    NOS_SIGNAL_RAISED           = 0x01,
    NOS_SIGNAL_CREATED          = 0x80
} nOS_SignalState;
#endif

#if (NOS_CONFIG_ALARM_ENABLE > 0)
typedef enum nOS_AlarmState
{
    NOS_ALARM_DELETED           = 0x00,
    NOS_ALARM_WAITING           = 0x01,
    NOS_ALARM_TRIGGERED         = 0x02,
    NOS_ALARM_CREATED           = 0x80
} nOS_AlarmState;
#endif

#include "nOSPort.h"

/* Port specific config checkup */
#ifdef NOS_USE_SEPARATE_CALL_STACK
 #if (NOS_CONFIG_TIMER_ENABLE > 0)
  #if (NOS_CONFIG_TIMER_THREAD_ENABLE > 0)
   #ifndef NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE
    #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE is not defined: must be higher than 0."
   #elif (NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE == 0)
    #error "nOSConfig.h: NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE is set to invalid value: must be higher than 0."
   #endif
  #else
   #undef NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE
  #endif
 #else
  #undef NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE
 #endif
#else
 #undef NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE
#endif

#ifdef NOS_USE_SEPARATE_CALL_STACK
 #if (NOS_CONFIG_SIGNAL_ENABLE > 0)
  #if (NOS_CONFIG_SIGNAL_THREAD_ENABLE > 0)
   #ifndef NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE
    #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE is not defined: must be higher than 0."
   #elif (NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE == 0)
    #error "nOSConfig.h: NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE is set to invalid value: must be higher than 0."
   #endif
  #else
   #undef NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE
  #endif
 #else
  #undef NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE
 #endif
#else
 #undef NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE
#endif

#ifdef NOS_DONT_USE_CONST
 #define NOS_CONST
#else
 #define NOS_CONST                  const
#endif

struct nOS_List
{
    nOS_Node            *head;
    nOS_Node            *tail;
};

struct nOS_Node
{
    nOS_Node            *prev;
    nOS_Node            *next;
    void                *payload;
};

struct nOS_Event
{
#if (NOS_CONFIG_SAFE > 0)
    nOS_EventType       type;
#endif
    nOS_List            waitList;
};

struct nOS_Thread
{
    nOS_Stack           *stackPtr;
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
    uint8_t             prio;
#endif
    int                 error;
    nOS_ThreadState     state;
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
    nOS_TickCounter     timeout;
#endif
    nOS_Event           *event;
    void                *ext;
#if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
    const char          *name;
#endif
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
    nOS_Event           joined;
#endif

    nOS_Node            readyWait;
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
    nOS_Node            tout;
#endif
#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
    nOS_Node            node;
#endif
};

#if (NOS_CONFIG_SEM_ENABLE > 0)
struct nOS_Sem
{
    nOS_Event           e;
    nOS_SemCounter      count;
    nOS_SemCounter      max;
};
#endif

#if (NOS_CONFIG_MUTEX_ENABLE > 0)
struct nOS_Mutex
{
    nOS_Event           e;
    nOS_Thread          *owner;
    nOS_MutexType       type;
    nOS_MutexCounter    count;
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
    uint8_t             prio;
    uint8_t             backup;
 #endif
};
#endif

#if (NOS_CONFIG_QUEUE_ENABLE > 0)
struct nOS_Queue
{
    nOS_Event           e;
    uint8_t             *buffer;
    uint8_t             bsize;
    nOS_QueueCounter    bmax;
    nOS_QueueCounter    bcount;
    nOS_QueueCounter    r;
    nOS_QueueCounter    w;
};
#endif

#if (NOS_CONFIG_FLAG_ENABLE > 0)
struct nOS_Flag
{
    nOS_Event           e;
    nOS_FlagBits        flags;
};

struct nOS_FlagContext
{
    nOS_FlagOption      opt;
    nOS_FlagBits        flags;
    nOS_FlagBits        *rflags;
};
#endif

#if (NOS_CONFIG_MEM_ENABLE > 0)
struct nOS_Mem
{
    nOS_Event           e;
    void                **blist;
 #if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
    void                *buffer;
    nOS_MemSize         bsize;
    nOS_MemCounter      bcount;
    nOS_MemCounter      bmax;
 #endif
};
#endif

#if (NOS_CONFIG_TIMER_ENABLE > 0)
struct nOS_Timer
{
    nOS_TimerState      state;
    nOS_TimerCounter    count;
    nOS_TimerCounter    reload;
    nOS_TimerCounter    overflow;
    nOS_TimerCallback   callback;
    void                *arg;
 #if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
    uint8_t             prio;
 #endif
    nOS_Node            node;
    nOS_Node            trig;
};
#endif

#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
struct nOS_Signal
{
    nOS_SignalState     state;
    nOS_SignalCallback  callback;
    void                *arg;
#if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
    uint8_t             prio;
#endif
    nOS_Node            node;
};
#endif

#if (NOS_CONFIG_TIME_ENABLE > 0)
struct nOS_TimeDate
{
    uint16_t            year;           /* From 1970 to ... */
    uint8_t             month;          /* From 1 (January) to 12 (December) */
    uint8_t             day;            /* From 1 to 31 */
    uint8_t             weekday;        /* From 1 (Monday) to 7 (Sunday) */
    uint8_t             hour;           /* From 0 to 23 */
    uint8_t             minute;         /* From 0 to 59 */
    uint8_t             second;         /* From 0 to 59 */
};
#endif

#if (NOS_CONFIG_ALARM_ENABLE > 0)
struct nOS_Alarm
{
    nOS_AlarmState      state;
    nOS_Time            time;
    nOS_AlarmCallback   callback;
    void                *arg;
    nOS_Node            node;
};
#endif

#if (NOS_CONFIG_BARRIER_ENABLE > 0)
struct nOS_Barrier
{
    nOS_Event           e;
    uint8_t             count;
    uint8_t             max;
};
#endif

#define NOS_NO_WAIT                 0
#if (NOS_CONFIG_TICK_COUNT_WIDTH == 8)
 #define NOS_TICK_COUNT_MAX         UINT8_MAX
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 16)
 #define NOS_TICK_COUNT_MAX         UINT16_MAX
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 32)
 #define NOS_TICK_COUNT_MAX         UINT32_MAX
#elif (NOS_CONFIG_TICK_COUNT_WIDTH == 64)
 #define NOS_TICK_COUNT_MAX         UINT64_MAX
#endif
#define NOS_WAIT_INFINITE           NOS_TICK_COUNT_MAX
#define NOS_TICKS_WAIT_MAX          (NOS_TICK_COUNT_MAX-1)

#define NOS_THREAD_PRIO_IDLE        0

#if (NOS_CONFIG_SEM_COUNT_WIDTH == 8)
 #define NOS_SEM_COUNT_MAX          UINT8_MAX
#elif (NOS_CONFIG_SEM_COUNT_WIDTH == 16)
 #define NOS_SEM_COUNT_MAX          UINT16_MAX
#elif (NOS_CONFIG_SEM_COUNT_WIDTH == 32)
 #define NOS_SEM_COUNT_MAX          UINT32_MAX
#elif (NOS_CONFIG_SEM_COUNT_WIDTH == 64)
 #define NOS_SEM_COUNT_MAX          UINT64_MAX
#endif

#if (NOS_CONFIG_MUTEX_COUNT_WIDTH == 8)
 #define NOS_MUTEX_COUNT_MAX        UINT8_MAX
#elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 16)
 #define NOS_MUTEX_COUNT_MAX        UINT16_MAX
#elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 32)
 #define NOS_MUTEX_COUNT_MAX        UINT32_MAX
#elif (NOS_CONFIG_MUTEX_COUNT_WIDTH == 64)
 #define NOS_MUTEX_COUNT_MAX        UINT64_MAX
#endif

#if (NOS_CONFIG_TIMER_COUNT_WIDTH == 8)
 #define NOS_TIMER_COUNT_MAX        UINT8_MAX
#elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 16)
 #define NOS_TIMER_COUNT_MAX        UINT16_MAX
#elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 32)
 #define NOS_TIMER_COUNT_MAX        UINT32_MAX
#elif (NOS_CONFIG_TIMER_COUNT_WIDTH == 64)
 #define NOS_TIMER_COUNT_MAX        UINT64_MAX
#endif

#define NOS_MUTEX_PRIO_INHERIT      0

#define NOS_FLAG_NONE               0
#define NOS_FLAG_TEST_ANY           false
#define NOS_FLAG_TEST_ALL           true

#ifdef NOS_PRIVATE
 #ifdef NOS_GLOBALS
  bool                      nOS_initialized = false;
  volatile bool             nOS_running = false;
 #else
  extern bool               nOS_initialized;
  extern volatile bool      nOS_running;
 #endif
 NOS_EXTERN nOS_Thread      nOS_idleHandle;
 NOS_EXTERN nOS_TickCounter nOS_tickCounter;
 NOS_EXTERN uint8_t         nOS_isrNestingCounter;
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
  NOS_EXTERN uint8_t        nOS_lockNestingCounter;
 #endif
 NOS_EXTERN nOS_Thread      *nOS_runningThread;
 NOS_EXTERN nOS_Thread      *nOS_highPrioThread;
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
  NOS_EXTERN nOS_List       nOS_readyThreadsList[NOS_CONFIG_HIGHEST_THREAD_PRIO+1];
 #else
  NOS_EXTERN nOS_List       nOS_readyThreadsList;
 #endif
 #if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
  NOS_EXTERN nOS_List        nOS_timeoutThreadsList;
 #endif
 #if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
  NOS_EXTERN nOS_List       nOS_allThreadsList;
 #endif

 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
  nOS_Thread*       nOS_FindHighPrioThread              (void);
  void              nOS_AppendThreadToReadyList         (nOS_Thread *thread);
  void              nOS_RemoveThreadFromReadyList       (nOS_Thread *thread);
 #else
  #define           nOS_FindHighPrioThread()            nOS_GetHeadOfList(&nOS_readyThreadsList)
  #define           nOS_AppendThreadToReadyList(t)      nOS_AppendToList(&nOS_readyThreadsList, &(t)->readyWait)
  #define           nOS_RemoveThreadFromReadyList(t)    nOS_RemoveFromList(&nOS_readyThreadsList, &(t)->readyWait)
 #endif
 nOS_Error          nOS_Schedule                        (void);

 #define            nOS_InitList(list)                  do{ (list)->head = NULL; (list)->tail = NULL; } while(0)
 #define            nOS_GetHeadOfList(list)             ((list)->head != NULL ? (list)->head->payload : NULL)
 void               nOS_AppendToList                    (nOS_List *list, nOS_Node *node);
 void               nOS_RemoveFromList                  (nOS_List *list, nOS_Node *node);
 void               nOS_RotateList                      (nOS_List *list);
 void               nOS_WalkInList                      (nOS_List *list, nOS_NodeHandler handler, void *arg);

 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
  void              nOS_SetThreadPrio                   (nOS_Thread *thread, uint8_t prio);
 #endif
 void               nOS_TickThread                      (void *payload, void *arg);
 void               nOS_WakeUpThread                    (nOS_Thread *thread, nOS_Error err);
 #if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
  int               nOS_ThreadWrapper                   (void *arg);
 #endif

 void               nOS_CreateEvent                     (nOS_Event *event
 #if (NOS_CONFIG_SAFE > 0)
                                                        ,nOS_EventType type
 #endif
                                                        );
 void               nOS_DeleteEvent                     (nOS_Event *event);
 void               nOS_BroadcastEvent                  (nOS_Event *event, nOS_Error err);
 nOS_Error          nOS_WaitForEvent                    (nOS_Event *event,
                                                         nOS_ThreadState state
 #if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                                                        ,nOS_TickCounter timeout
 #endif
                                                        );
 nOS_Thread*        nOS_SendEvent                       (nOS_Event *event, nOS_Error err);

 #if (NOS_CONFIG_TIMER_ENABLE > 0)
  void              nOS_InitTimer                       (void);
 #endif

 #if (NOS_CONFIG_SIGNAL_ENABLE > 0)
  void              nOS_InitSignal                      (void);
 #endif

 #if (NOS_CONFIG_TIME_ENABLE > 0)
  void              nOS_InitTime                        (void);
 #endif

 #if (NOS_CONFIG_ALARM_ENABLE > 0)
  void              nOS_InitAlarm                       (void);
 #endif
#endif

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name         : nOS_Init                                                                                            *
 *                                                                                                                    *
 * Description  : Initialize nOS scheduler and enabled services.                                                      *
 *                                                                                                                    *
 * Return       : Error code.                                                                                         *
 *   NOS_OK     : Initialization successfully completed.                                                              *
 *   NOS_E_INIT : Scheduler already initialized.                                                                      *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. This is the first nOS function that the application should call, else the behavior is undefined.              *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_Error           nOS_Init                            (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_Start                                                                                        *
 *                                                                                                                    *
 * Description     : Enable context switching.                                                                        *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Initialization successfully completed.                                                           *
 *   NOS_E_RUNNING : Context switching is already enabled.                                                            *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Call this function when you are ready to allow context switching.                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_Error           nOS_Start                           (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name           : nOS_Yield                                                                                         *
 *                                                                                                                    *
 * Description    : Request an immediate context switch from currently running thread to highest priority ready to    *
 *                  run thread.                                                                                       *
 *                                                                                                                    *
 * Return         : Error code.                                                                                       *
 *   NOS_OK       : Yielding successfully completed.                                                                  *
 *   NOS_E_ISR    : Can't yield from interrupt service routine.                                                       *
 *   NOS_E_LOCKED : Can't yield from a scheduler locked section.                                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_Error           nOS_Yield                           (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_Tick                                                                                             *
 *                                                                                                                    *
 * Description : Send ticks to scheduler and enabled services. Can send single tick like in systick handler or        *
 *               multiple ticks when systick has been disabled for a long time like when recovering from MCU sleep.   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   ticks     : Number of ticks to do.                                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Must be called x times per second by the application if needed.                                               *
 *        x = NOS_CONFIG_TICKS_PER_SECOND                                                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
void                nOS_Tick                            (nOS_TickCounter ticks);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_GetTickCount                                                                                     *
 *                                                                                                                    *
 * Description : Get scheduler free running tick counter. Can be used to compute number of ticks passed since last    *
 *               event or create periodic task in combination with nOS_SleepUntil.                                    *
 *                                                                                                                    *
 * Return      : Tick counter.                                                                                        *
 *                 See note 1                                                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width is determined by NOS_CONFIG_TICK_COUNT_WIDTH.                                                      *
 *   2. This is a free running counter that will certainly overflow.                                                  *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_TickCounter     nOS_GetTickCount                    (void);

#if defined(NOS_CONFIG_TICKS_PER_SECOND) && (NOS_CONFIG_TICKS_PER_SECOND > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_MsToTicks                                                                                        *
 *                                                                                                                    *
 * Description : Convert a number of milliseconds in number of ticks. Can be used for timer reload value.             *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   ms        : Number of milliseconds.                                                                              *
 *                                                                                                                    *
 * Return      : Number of ticks.                                                                                     *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can return a higher count than nOS_TickCounter if NOS_CONFIG_TICK_COUNT_WIDTH is less than 32 bits.           *
 *                                                                                                                    *
 **********************************************************************************************************************/
 uint32_t           nOS_MsToTicks                       (uint16_t ms);
#endif

#if (NOS_CONFIG_SLEEP_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name           : nOS_Sleep                                                                                         *
 *                                                                                                                    *
 * Description    : Place currently running thread in sleeping state for specified number of ticks.                   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   ticks        : Number of ticks to wait.                                                                          *
 *                                                                                                                    *
 * Return         : Error code.                                                                                       *
 *   NOS_OK       : Running thread successfully sleeping.                                                             *
 *   NOS_E_ISR    : Can't sleep from interrupt service routine.                                                       *
 *   NOS_E_LOCKED : Can't sleep from scheduler locked section.                                                        *
 *   NOS_E_IDLE   : Can't sleep from main thread.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_Sleep                           (nOS_TickCounter ticks);

 #if defined(NOS_CONFIG_TICKS_PER_SECOND) && (NOS_CONFIG_TICKS_PER_SECOND > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name           : nOS_SleepMs                                                                                       *
 *                                                                                                                    *
 * Description    : Place currently running thread in sleeping state for specified number of milliseconds.            *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   ms           : Number of milliseconds to wait.                                                                   *
 *                                                                                                                    *
 * Return         : Error code.                                                                                       *
 *   NOS_OK       : Running thread successfully sleeping.                                                             *
 *   NOS_E_ISR    : Can't sleep from interrupt service routine.                                                       *
 *   NOS_E_LOCKED : Can't sleep from scheduler locked section.                                                        *
 *   NOS_E_IDLE   : Can't sleep from main thread.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
  nOS_Error         nOS_SleepMs                         (uint16_t ms);
 #endif
#endif

#if (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name           : nOS_SleepUntil                                                                                    *
 *                                                                                                                    *
 * Description    : Place currently running thread in sleeping state until reaching specified tick counter. Can be    *
 *                  used in combination with nOS_GetTickCount to create periodic task.                                *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   tick         : Absolute tick counter to wait.                                                                    *
 *                                                                                                                    *
 * Return         : Error code.                                                                                       *
 *   NOS_OK       : Running thread successfully sleeping.                                                             *
 *   NOS_E_ISR    : Can't sleep from interrupt service routine.                                                       *
 *   NOS_E_LOCKED : Can't sleep from scheduler locked section.                                                        *
 *   NOS_E_IDLE   : Can't sleep from main thread.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SleepUntil                      (nOS_TickCounter tick);
#endif

#if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name             : nOS_SchedLock                                                                                   *
 *                                                                                                                    *
 * Description      : Lock the scheduler to disable context switching without disabling interrupts.                   *
 *                                                                                                                    *
 * Return           : Error code.                                                                                     *
 *   NOS_OK         : Scheduler successfully locked.                                                                  *
 *   NOS_E_ISR      : Can't lock scheduler from interrupt service routine.                                            *
 *   NOS_E_OVERFLOW : Scheduler locked too many times.                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. For each lock called, the same number of unlock should be called to unlock the scheduler.                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SchedLock                       (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_SchedUnlock                                                                                *
 *                                                                                                                    *
 * Description       : Unlock the scheduler and re-enable context switching.                                          *
 *                                                                                                                    *
 * Return            : Error code.                                                                                    *
 *   NOS_OK          : Scheduler successfully unlocked.                                                               *
 *   NOS_E_ISR       : Can't unlock scheduler from interrupt service routine.                                         *
 *   NOS_E_UNDERFLOW : Scheduler unlocked too many times.                                                             *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. For each lock called, the same number of unlock should be called to unlock the scheduler.                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SchedUnlock                     (void);
#endif

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_GetRunningThread                                                                           *
 *                                                                                                                    *
 * Description       : Return a pointer to nOS_Thread object of current running thread.                               *
 *                                                                                                                    *
 * Return            : Pointer to nOS_Thread.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_Thread *        nOS_GetRunningThread                (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_ThreadCreate                                                                               *
 *                                                                                                                    *
 * Description       : Create a new thread and add it to the list of threads managed by the scheduler.                *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   thread          : Pointer to nOS_Thread object allocated by the application.                                     *
 *   entry           : Pointer to the thread entry function. It shall be implemented has a never ending loop.         *
 *   arg             : Pointer that will be used as parameter when thread will run.                                   *
 *   stack           : Pointer to an array of nOS_Stack entries allocated by the application.                         *
 *   ssize           : Total size of the stack in number of nOS_Stack entries.                                        *
 *   cssize          : Size of the call stack to reserve on stack in number of call entries.                          *
 *                       See note 1                                                                                   *
 *   prio            : Priority of the thread: 0 <= prio <= NOS_CONFIG_HIGHEST_THREAD_PRIO.                           *
 *                       See note 2                                                                                   *
 *   state           : State of the thread at creation.                                                               *
 *                       NOS_THREAD_READY     : Thread will be added in list of threads that are ready to run.        *
 *                       NOS_THREAD_SUSPENDED : Thread will be created, but kept in suspended state until another     *
 *                                              thread resume it explicitly.                                          *
 *                       See note 3                                                                                   *
 *   name            : Pointer to ascii string representing the name of the thread (can be useful for debugging).     *
 *                       See note 4                                                                                   *
 *                                                                                                                    *
 * Return            : Error code.                                                                                    *
 *   NOS_OK          : Thread successfully created.                                                                   *
 *   NOS_E_INV_OBJ   : Pointer to nOS_Thread object is invalid.                                                       *
 *   NOS_E_INV_VAL   : Invalid parameter(s) (can be an invalid thread entry, stack array, stack size and/or call      *
 *                     stack size).                                                                                   *
 *   NOS_E_INV_PRIO  : Priority is higher than NOS_CONFIG_HIGHEST_THREAD_PRIO.                                        *
 *   NOS_E_INV_STATE : State of the thread is invalid.                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available on AVR platform with IAR compiler.                                                             *
 *   2. Not available if NOS_CONFIG_HIGHEST_THREAD_PRIO is defined to 0.                                              *
 *   3. If NOS_CONFIG_THREAD_SUSPEND_ENABLE if defined to 0, this parameter is not available and threads will always  *
 *      be created in ready state.                                                                                    *
 *   4. Not available if NOS_CONFIG_THREAD_NAME_ENABLE is defined to 0.                                               *
 *                                                                                                                    *
 **********************************************************************************************************************/
nOS_Error           nOS_ThreadCreate                    (nOS_Thread *thread,
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
                                                        );

#if (NOS_CONFIG_THREAD_DELETE_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_ThreadDelete                                                                                 *
 *                                                                                                                    *
 * Description     : Delete thread and remove it from ready to run list or any waiting list managed by the scheduler. *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   thread        : Pointer to nOS_Thread object.                                                                    *
 *                     See note 1.                                                                                    *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Thread successfully deleted.                                                                     *
 *   NOS_E_INV_OBJ : Pointer to nOS_Thread object is invalid.                                                         *
 *   NOS_E_LOCKED  : Can't delete running thread from scheduler locked section.                                       *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Pointer can be NULL to access the running thread.                                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadDelete                    (nOS_Thread *thread);
#endif

#if (NOS_CONFIG_THREAD_ABORT_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_ThreadAbort                                                                                *
 *                                                                                                                    *
 * Description       : Abort waiting operation of thread and remove it from the event waiting list.                   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   thread          : Pointer to nOS_Thread object.                                                                  *
 *                                                                                                                    *
 * Return            : Error code.                                                                                    *
 *   NOS_OK          : Thread have successfully abort is waiting operation.                                           *
 *   NOS_E_INV_OBJ   : Pointer to nOS_Thread object is invalid.                                                       *
 *   NOS_E_INV_STATE : Thread not currently in waiting state.                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadAbort                     (nOS_Thread *thread);
#endif

#if (NOS_CONFIG_THREAD_SUSPEND_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_ThreadSuspend                                                                              *
 *                                                                                                                    *
 * Description       : Suspend thread and remove it from ready to run list if applicable. Use this function with high *
 *                     care, if thread is holding resources, it can produce a deadlock if other threads need these    *
 *                     resources.                                                                                     *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   thread          : Pointer to nOS_Thread object.                                                                  *
 *                       See note 1.                                                                                  *
 *                                                                                                                    *
 * Return            : Error code.                                                                                    *
 *   NOS_OK          : Thread successfully suspended.                                                                 *
 *   NOS_E_INV_OBJ   : Pointer to nOS_Thread object is invalid.                                                       *
 *   NOS_E_INV_STATE : Thread is already in suspended state.                                                          *
 *   NOS_E_LOCKED    : Can't suspend running thread from scheduler locked section.                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Pointer can be NULL to access the running thread.                                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadSuspend                   (nOS_Thread *thread);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name              : nOS_ThreadResume                                                                               *
 *                                                                                                                    *
 * Description       : Resume previously suspended thread and add it to ready to run list if applicable.              *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   thread          : Pointer to nOS_Thread object.                                                                  *
 *                                                                                                                    *
 * Return            : Error code.                                                                                    *
 *   NOS_OK          : Thread successfully resumed.                                                                   *
 *   NOS_E_INV_OBJ   : Pointer to nOS_Thread object is invalid.                                                       *
 *   NOS_E_INV_STATE : Thread is not in suspended state.                                                              *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadResume                    (nOS_Thread *thread);

#if (NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name           : nOS_ThreadSuspendAll                                                                              *
 *                                                                                                                    *
 * Description    : Suspend all threads (except main thread) and remove them from ready ro run list.                  *
 *                                                                                                                    *
 * Return         : Error code.                                                                                       *
 *   NOS_OK       : All threads successfully suspended.                                                               *
 *   NOS_E_LOCKED : Can't lock all threads from scheduler locked section if not called from main thread.              *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadSuspendAll                (void);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_ThreadResumeAll                                                                                  *
 *                                                                                                                    *
 * Description : Resume all suspended threads and add them to ready to run list.                                      *
 *                                                                                                                    *
 * Return      : Error code.                                                                                          *
 *   NOS_OK    : All suspended threads successfully resumed.                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_ThreadResumeAll                 (void);
#endif

#endif
#if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0) && (NOS_CONFIG_THREAD_SET_PRIO_ENABLE > 0)
 int16_t            nOS_ThreadGetPriority               (nOS_Thread *thread);
 nOS_Error          nOS_ThreadSetPriority               (nOS_Thread *thread, uint8_t prio);
#endif
#if (NOS_CONFIG_THREAD_NAME_ENABLE > 0)
 const char*        nOS_ThreadGetName                   (nOS_Thread *thread);
 nOS_Error          nOS_ThreadSetName                   (nOS_Thread *thread, const char *name);
#endif
#if (NOS_CONFIG_THREAD_JOIN_ENABLE > 0)
 nOS_Error          nOS_ThreadJoin                      (nOS_Thread *thread, int *ret, nOS_TickCounter timeout);
#endif

#if (NOS_CONFIG_SEM_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_SemCreate                                                                                    *
 *                                                                                                                    *
 * Description     : Create a new semaphore object.                                                                   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   sem           : Pointer to semaphore object.                                                                     *
 *   count         : Initial count of semaphore.                                                                      *
 *   max           : Maximum count of semaphore.                                                                      *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Semaphore successfully created.                                                                  *
 *   NOS_E_INV_OBJ : Pointer to semaphore object is invalid.                                                          *
 *   NOS_E_INV_VAL : Initial count is higher than defined maximum.                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Semaphore object must be created before using it, else the behavior is undefined.                             *
 *   2. Must be called one time only for each semaphore object.                                                       *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SemCreate                       (nOS_Sem *sem, nOS_SemCounter count, nOS_SemCounter max);

 #if (NOS_CONFIG_SEM_DELETE_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_SemDelete                                                                                    *
 *                                                                                                                    *
 * Description     : Delete semaphore object and wake up all waiting threads if any.                                  *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   sem           : Pointer to semaphore object.                                                                     *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Semaphore successfully deleted.                                                                  *
 *   NOS_E_INV_OBJ : Pointer to semaphore object is invalid.                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
  nOS_Error         nOS_SemDelete                       (nOS_Sem *sem);
 #endif

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_SemTake                                                                                      *
 *                                                                                                                    *
 * Description     : Take semaphore pointed by object pointer. If not available, calling thread will be placed in     *
 *                   event's waiting list for number of ticks specified by timeout. If semaphore is not available in  *
 *                   required time, an error will be returned and semaphore will be left unchanged.                   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   sem           : Pointer to semaphore object.                                                                     *
 *   timeout       : Timeout value.                                                                                   *
 *                     NOS_NO_WAIT                     : Don't wait if the semaphore is not available.                *
 *                     0 > timeout < NOS_WAIT_INFINITE : Maximum number of ticks to wait for the semaphore to become  *
 *                                                       available.                                                   *
 *                     NOS_WAIT_INFINITE               : Wait indefinitely until the semaphore become available.      *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Requested semaphore have been successfully taken.                                                *
 *   NOS_E_INV_OBJ : Pointer to semaphore object is invalid.                                                          *
 *   NOS_E_AGAIN   : Semaphore is unavailable (happens when timeout equal NOS_NO_WAIT).                               *
 *   NOS_E_ISR     : Can't wait from interrupt service routine.                                                       *
 *   NOS_E_LOCKED  : Can't wait from scheduler locked section.                                                        *
 *   NOS_E_IDLE    : Can't wait from main thread (idle).                                                              *
 *   NOS_E_TIMEOUT : Semaphore has not been given before reaching timeout.                                            *
 *   NOS_E_DELETED : Semaphore object has been deleted.                                                               *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SemTake                         (nOS_Sem *sem, nOS_TickCounter timeout);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_SemGive                                                                                      *
 *                                                                                                                    *
 * Description     : Give semaphore pointed by object pointer. If a thread is waiting, replace it in ready list with  *
 *                   operation successfull code. If no thread is waiting, increment semaphore count if lower than     *
 *                   maximum available count, else return an overflow error.                                          *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   sem           : Pointer to semaphore object.                                                                     *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Requested semaphore have been successfully taken.                                                *
 *   NOS_E_INV_OBJ : Pointer to semaphore object is invalid.                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_SemGive                         (nOS_Sem *sem);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_SemIsAvailable                                                                               *
 *                                                                                                                    *
 * Description     : Return availability of semaphore.                                                                *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   sem           : Pointer to semaphore object.                                                                     *
 *                                                                                                                    *
 * Return          : TRUE if semaphore count is higher than 0, else FALSE.                                            *
 *                                                                                                                    *
 **********************************************************************************************************************/
 bool               nOS_SemIsAvailable                  (nOS_Sem *sem);
#endif

#if (NOS_CONFIG_MUTEX_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_MutexCreate                                                                                  *
 *                                                                                                                    *
 * Description     : Create a new mutex object.                                                                       *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mutex         : Pointer to mutex object.                                                                         *
 *   type          : Type of mutex to create.                                                                         *
 *                     NOS_MUTEX_NORMAL    : Standard mutex (like binary semaphore).                                  *
 *                     NOS_MUTEX_RECURSIVE : Mutex that can be locked recursively.                                    *
 *   prio          : Priority of mutex.                                                                               *
 *                     NOS_MUTEX_PRIO_INHERIT : Mutex owner inherit higher prio from other threads that try to lock   *
 *                                              this mutex.                                                           *
 *                     prio > 0               : Mutex owner increase its prio to this value when it lock the mutex    *
 *                                              (immediate ceiling protocol).                                         *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Mutex successfully created.                                                                      *
 *   NOS_E_INV_OBJ : Pointer to mutex object is invalid.                                                              *
 *   NOS_E_INV_VAL : Type of mutex is invalid.                                                                        *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Mutex object must be created before using it, else the behavior is undefined.                                 *
 *   2. Must be called one time only for each mutex object.                                                           *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_MutexCreate                     (nOS_Mutex *mutex,
                                                         nOS_MutexType type
 #if (NOS_CONFIG_HIGHEST_THREAD_PRIO > 0)
                                                        ,uint8_t prio
 #endif
                                                        );
 #if (NOS_CONFIG_MUTEX_DELETE_ENABLE > 0)
  nOS_Error         nOS_MutexDelete                     (nOS_Mutex *mutex);
 #endif
 nOS_Error          nOS_MutexLock                       (nOS_Mutex *mutex, nOS_TickCounter timeout);
 nOS_Error          nOS_MutexUnlock                     (nOS_Mutex *mutex);
 bool               nOS_MutexIsLocked                   (nOS_Mutex *mutex);
 nOS_Thread*        nOS_MutexGetOwner                   (nOS_Mutex *mutex);
#endif

#if (NOS_CONFIG_QUEUE_ENABLE > 0)
 nOS_Error          nOS_QueueCreate                     (nOS_Queue *queue, void *buffer, uint8_t bsize, nOS_QueueCounter bmax);
 #if (NOS_CONFIG_QUEUE_DELETE_ENABLE > 0)
  nOS_Error         nOS_QueueDelete                     (nOS_Queue *queue);
 #endif
 nOS_Error          nOS_QueueRead                       (nOS_Queue *queue, void *block, nOS_TickCounter timeout);
 nOS_Error          nOS_QueuePeek                       (nOS_Queue *queue, void *block);
 nOS_Error          nOS_QueueWrite                      (nOS_Queue *queue, void *block, nOS_TickCounter timeout);
 nOS_Error          nOS_QueueFlush                      (nOS_Queue *queue, nOS_QueueCallback callback);
 bool               nOS_QueueIsEmpty                    (nOS_Queue *queue);
 bool               nOS_QueueIsFull                     (nOS_Queue *queue);
 nOS_QueueCounter   nOS_QueueGetCount                   (nOS_Queue *queue);
#endif

#if (NOS_CONFIG_FLAG_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_FlagCreate                                                                                   *
 *                                                                                                                    *
 * Description     : Create a flag event object and initialize it with given flags.                                   *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   flag          : Pointer to flag object.                                                                          *
 *   flags         : Initial values.                                                                                  *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Flag successfully created.                                                                       *
 *   NOS_E_INV_OBJ : Pointer to flag object is invalid.                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Flag object must be created before using it, else the behavior is undefined.                                  *
 *   2. Must be called one time only for each flag object.                                                            *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_FlagCreate                      (nOS_Flag *flag, nOS_FlagBits flags);

 #if (NOS_CONFIG_FLAG_DELETE_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_FlagDelete                                                                                   *
 *                                                                                                                    *
 * Description     : Delete a flag event object and wake up all waiting threads.                                      *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   flag          : Pointer to flag object.                                                                          *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Flag successfully deleted.                                                                       *
 *   NOS_E_INV_OBJ : Pointer to flag object is invalid.                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Flag object must be created before, else the behavior is undefined.                                           *
 *   2. Flag object must not be used after deletion, else the behavior is undefined.                                  *
 *                                                                                                                    *
 **********************************************************************************************************************/
  nOS_Error         nOS_FlagDelete                      (nOS_Flag *flag);
 #endif

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_FlagWait                                                                                     *
 *                                                                                                                    *
 * Description     : Wait on flag object for given flags. If flags are NOT set, calling thread will be placed in      *
 *                   event's waiting list for number of ticks specified by timeout. If flags are set before end of    *
 *                   timeout, res will contain flags that have awoken the thread. If caller specify                   *
 *                   NOS_FLAG_CLEAR_ON_EXIT, only awoken flags will be cleared.                                       *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   flag          : Pointer to flag object.                                                                          *
 *   flags         : All flags to wait.                                                                               *
 *   res           : Pointer where to store awoken flags if needed.                                                   *
 *                     See note 1                                                                                     *
 *   opt           : Waiting options.                                                                                 *
 *                     NOS_FLAG_WAIT_ALL      : Wait for all flags to be set.                                         *
 *                     NOS_FLAG_WAIT_ANY      : Wait for any flags to be set.                                         *
 *                   Altering options.                                                                                *
 *                     NOS_FLAG_CLEAR_ON_EXIT : Clear awoken flags.                                                   *
 *                       See note 2                                                                                   *
 *   timeout       : Timeout value.                                                                                   *
 *                     NOS_NO_WAIT                     : Don't wait if flags are not set.                             *
 *                     0 > timeout < NOS_WAIT_INFINITE : Maximum number of ticks to wait for flags to be set.         *
 *                     NOS_WAIT_INFINITE               : Wait indefinitely until flags are set.                       *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Requested flags have been set in required time.                                                  *
 *   NOS_E_INV_OBJ : Pointer to flag object is invalid.                                                               *
 *   NOS_E_AGAIN   : Flags are not in required state (happens when timeout equal NOS_NO_WAIT).                        *
 *   NOS_E_ISR     : Can't wait from interrupt service routine.                                                       *
 *   NOS_E_LOCKED  : Can't wait from scheduler locked section.                                                        *
 *   NOS_E_IDLE    : Can't wait from main thread (idle).                                                              *
 *   NOS_E_TIMEOUT : Flags have not been set before reaching timeout.                                                 *
 *   NOS_E_DELETED : Flag object has been deleted.                                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only valid if returned error code is NOS_OK. Otherwise, res is unchanged.                                     *
 *   2. One waiting option can be OR'ed with altering option if needed.                                               *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_FlagWait                        (nOS_Flag *flag, nOS_FlagBits flags, nOS_FlagBits *res,
                                                         nOS_FlagOption opt, nOS_TickCounter timeout);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_FlagSend                                                                                     *
 *                                                                                                                    *
 * Description     : Set/clear given flags in flag object. Many flags can be set/clear atomically. Just sent flags    *
 *                   can be clear immediately if waiting threads had requested NOS_FLAG_CLEAR_ON_EXIT.                *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   flag          : Pointer to flag object.                                                                          *
 *   flags         : All flags to set/clear depending on mask.                                                        *
 *   mask          : Mask containing which flags to affect. If corresponding bit in flags is 0, this bit will be      *
 *                   cleared. If corresponding bit in flags is 1, this bit will be set.                               *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Flags successfully sent.                                                                         *
 *   NOS_E_INV_OBJ : Pointer to flag object is invalid.                                                               *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_FlagSend                        (nOS_Flag *flag, nOS_FlagBits flags, nOS_FlagBits mask);
#endif

#if (NOS_CONFIG_MEM_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name            : nOS_MemCreate                                                                                    *
 *                                                                                                                    *
 * Description     : Create a fixed-sized array of memory block.                                                      *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mem           : Pointer to mem object allocated by the application.                                              *
 *   buffer        : Pointer to array of memory allocated by the application that will contains all the blocks.       *
 *                     See note 1, 2                                                                                  *
 *   bsize         : Size of one block of memory.                                                                     *
 *                     See note 3                                                                                     *
 *   bmax          : Maximum number of blocks available.                                                              *
 *                     See note 4                                                                                     *
 *                                                                                                                    *
 * Return          : Error code.                                                                                      *
 *   NOS_OK        : Memory successfully created.                                                                     *
 *   NOS_E_INV_OBJ : Pointer to mem object is invalid.                                                                *
 *   NOS_E_NULL    : Pointer to array of memory is invalid.                                                           *
 *   NOS_E_INV_VAL : Invalid parameter(s) (too small block size, buffer not aligned in memory and/or no blocks        *
 *                   available).                                                                                      *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Shall be large enough to keep bmax blocks of bsize bytes per block.                                           *
 *   2. buffer can't be shared between different mem object.                                                          *
 *   3. Shall be large enough to keep a generic pointer (void*) on target platform.                                   *
 *   4. Shall be higher than 0.                                                                                       *
 *   5. Mem object must be created before using it, otherwise the behavior is undefined.                              *
 *   6. Must be called one time only for each mem object.                                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_MemCreate                       (nOS_Mem *mem, void *buffer, nOS_MemSize bsize, nOS_MemCounter bmax);

 #if (NOS_CONFIG_MEM_DELETE_ENABLE > 0)
  nOS_Error         nOS_MemDelete                       (nOS_Mem *mem);
 #endif

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_MemAlloc                                                                                         *
 *                                                                                                                    *
 * Description : Try to take one block from memory array of mem. If no block available, calling thread will be        *
 *               removed from list of ready to run threads and be placed in list of waiting threads for number of     *
 *               ticks specified by timeout. If a block of memory is freed before end of timeout, thread will be      *
 *               awoken and pointer to memory block will be returned.                                                 *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mem       : Pointer to mem object.                                                                               *
 *   timeout   : Timeout value.                                                                                       *
 *                 NOS_NO_WAIT                     : Don't wait if no blocks available.                               *
 *                 0 > timeout < NOS_WAIT_INFINITE : Maximum number of ticks to wait until a block became available.  *
 *                 NOS_WAIT_INFINITE               : Wait indefinitely until a block became available.                *
 *                                                                                                                    *
 * Return      : Pointer to allocated block of memory.                                                                *
 *   == NULL   : No block available.                                                                                  *
 *   != NULL   : Pointer to newly allocated block of memory.                                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Mem object shall be created before trying to allocate a block.                                                *
 *   2. Caller is responsible to free the block when memory is no longer needed.                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
 void*              nOS_MemAlloc                        (nOS_Mem *mem, nOS_TickCounter timeout);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name             : nOS_MemFree                                                                                     *
 *                                                                                                                    *
 * Description      : Free a previously allocated block of memory.                                                    *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mem            : Pointer to mem object.                                                                          *
 *   block          : Pointer to previously allocated block.                                                          *
 *                                                                                                                    *
 * Return           : Error code.                                                                                     *
 *   NOS_OK         : Memory block has been freed with success.                                                       *
 *   NOS_E_INV_OBJ  : Pointer to mem object is invalid.                                                               *
 *   NOS_E_INV_VAL  : Pointer to block is outside mem defined range.                                                  *
 *                      See note 1                                                                                    *
 *   NOS_E_OVERFLOW : Too much block has been freed or block is already free.                                         *
 *                      See note 1, 2                                                                                 *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available if NOS_CONFIG_MEM_SANITY_CHECK_ENABLE is defined to 1.                                         *
 *   2. Never suppose to happen normally, can be a sign of corruption.                                                *
 *   3. Do not continue to use memory block after it has been freed.                                                  *
 *                                                                                                                    *
 **********************************************************************************************************************/
 nOS_Error          nOS_MemFree                         (nOS_Mem *mem, void *block);

/**********************************************************************************************************************
 *                                                                                                                    *
 * Name        : nOS_MemIsAvailable                                                                                   *
 *                                                                                                                    *
 * Description : Check if at least one block of memory is available.                                                  *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mem       : Pointer to mem object.                                                                               *
 *                                                                                                                    *
 * Return      : Block availability.                                                                                  *
 *   false     : No block of memory is currently available.                                                           *
 *   true      : At least one block of memory is available.                                                           *
 *                                                                                                                    *
 **********************************************************************************************************************/
 bool               nOS_MemIsAvailable                  (nOS_Mem *mem);
#endif

#if (NOS_CONFIG_TIMER_ENABLE > 0)
 void               nOS_TimerTick                       (nOS_TickCounter ticks);
 void               nOS_TimerProcess                    (void);
 nOS_Error          nOS_TimerCreate                     (nOS_Timer *timer,
                                                         nOS_TimerCallback callback,
                                                         void *arg,
                                                         nOS_TimerCounter reload,
                                                         nOS_TimerMode mode
 #if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
                                                        ,uint8_t prio
 #endif
                                                        );
 #if (NOS_CONFIG_TIMER_DELETE_ENABLE > 0)
  nOS_Error         nOS_TimerDelete                     (nOS_Timer *timer);
 #endif
 nOS_Error          nOS_TimerStart                      (nOS_Timer *timer);
 nOS_Error          nOS_TimerStop                       (nOS_Timer *timer, bool instant);
 nOS_Error          nOS_TimerRestart                    (nOS_Timer *timer, nOS_TimerCounter reload);
 nOS_Error          nOS_TimerPause                      (nOS_Timer *timer);
 nOS_Error          nOS_TimerContinue                   (nOS_Timer *timer);
 nOS_Error          nOS_TimerSetReload                  (nOS_Timer *timer, nOS_TimerCounter reload);
 nOS_Error          nOS_TimerSetCallback                (nOS_Timer *timer, nOS_TimerCallback callback, void *arg);
 nOS_Error          nOS_TimerSetMode                    (nOS_Timer *timer, nOS_TimerMode mode);
 #if (NOS_CONFIG_TIMER_HIGHEST_PRIO > 0)
  nOS_Error         nOS_TimerSetPrio                    (nOS_Timer *timer, uint8_t prio);
 #endif
 bool               nOS_TimerIsRunning                  (nOS_Timer *timer);
#endif

#if (NOS_CONFIG_SIGNAL_ENABLE > 0)
 void               nOS_SignalProcess                   (void);
 nOS_Error          nOS_SignalCreate                    (nOS_Signal *signal,
                                                         nOS_SignalCallback callback
 #if (NOS_CONFIG_SIGNAL_HIGHEST_PRIO > 0)
                                                        ,uint8_t prio
 #endif
                                                        );
 #if (NOS_CONFIG_SIGNAL_DELETE_ENABLE > 0)
  nOS_Error         nOS_SignalDelete                    (nOS_Signal *signal);
 #endif
 nOS_Error          nOS_SignalSend                      (nOS_Signal *signal, void *arg);
 nOS_Error          nOS_SignalSetCallback               (nOS_Signal *signal, nOS_SignalCallback callback);
 bool               nOS_SignalIsRaised                  (nOS_Signal *signal);
#endif

#if (NOS_CONFIG_TIME_ENABLE > 0)
 void               nOS_TimeTick                        (nOS_TickCounter ticks);
 nOS_Time           nOS_TimeGet                         (void);
 nOS_Error          nOS_TimeSet                         (nOS_Time time);
 nOS_TimeDate       nOS_TimeConvert                     (nOS_Time time);
 #if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
  nOS_Error         nOS_TimeWait                        (nOS_Time time);
 #endif
 bool               nOS_TimeIsLeapYear                  (uint16_t year);
 uint16_t           nOS_TimeGetDaysPerYear              (uint16_t year);
 uint8_t            nOS_TimeGetDaysPerMonth             (uint8_t month, uint16_t year);
 nOS_TimeDate       nOS_TimeDateGet                     (void);
 nOS_Error          nOS_TimeDateSet                     (nOS_TimeDate timedate);
 nOS_Time           nOS_TimeDateConvert                 (nOS_TimeDate timedate);
 #if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
  nOS_Error         nOS_TimeDateWait                    (nOS_TimeDate timedate);
 #endif
#endif

#if (NOS_CONFIG_ALARM_ENABLE > 0)
 void               nOS_AlarmTick                       (void);
 void               nOS_AlarmProcess                    (void);
 nOS_Error          nOS_AlarmCreate                     (nOS_Alarm *alarm, nOS_AlarmCallback callback, void *arg, nOS_Time time);
 #if (NOS_CONFIG_ALARM_DELETE_ENABLE > 0)
  nOS_Error         nOS_AlarmDelete                     (nOS_Alarm *alarm);
 #endif
 nOS_Error          nOS_AlarmSetTime                    (nOS_Alarm *alarm, nOS_Time time);
 nOS_Error          nOS_AlarmSetCallback                (nOS_Alarm *alarm, nOS_AlarmCallback callback, void *arg);
#endif

#if (NOS_CONFIG_BARRIER_ENABLE > 0)
 nOS_Error          nOS_BarrierCreate                   (nOS_Barrier *barrier, uint8_t max);
 #if (NOS_CONFIG_BARRIER_DELETE_ENABLE > 0)
  nOS_Error         nOS_BarrierDelete                   (nOS_Barrier *barrier);
 #endif
 nOS_Error          nOS_BarrierWait                     (nOS_Barrier *barrier);
#endif

#ifdef __cplusplus
}
#endif

#endif /* NOS_H */
