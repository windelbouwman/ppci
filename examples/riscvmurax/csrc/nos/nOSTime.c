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

#if (NOS_CONFIG_TIME_ENABLE > 0)

#define IS_LEAP_YEAR(y)     (((((y) % 4) == 0) && (((y) % 100) != 0)) || (((y) % 400) == 0))
#define DAYS_PER_YEAR(y)    (IS_LEAP_YEAR(y)?366:365)
#define DAYS_PER_MONTH(m,y) ((IS_LEAP_YEAR(y)&&((m)==2))?29:_daysPerMonth[(m)-1])

#if (NOS_CONFIG_TIME_TICKS_PER_SECOND > 1)
 static uint16_t            _prescaler;
#endif
static nOS_Time             _time;
#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
 static nOS_Event           _event;
#endif
static NOS_CONST uint8_t    _daysPerMonth[12] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};

#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
static void _TickTime(void *payload, void *arg)
{
    nOS_Thread  *thread = (nOS_Thread *)payload;
    nOS_Time    time    = *(nOS_Time *)thread->ext;

    /* Avoid warning */
    NOS_UNUSED(arg);

    if (time >= _time) {
        nOS_WakeUpThread(thread, NOS_OK);
    }
}
#endif

void nOS_InitTime (void)
{
#if (NOS_CONFIG_TIME_TICKS_PER_SECOND > 1)
    _prescaler  = 0;
#endif
    _time       = 0;
#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
    nOS_CreateEvent(&_event
 #if (NOS_CONFIG_SAFE > 0)
                   ,NOS_EVENT_BASE
 #endif
                   );
#endif
}

void nOS_TimeTick (nOS_TickCounter ticks)
{
    nOS_StatusReg   sr;
    nOS_Time        dt;

    nOS_EnterCritical(sr);
#if (NOS_CONFIG_TIME_TICKS_PER_SECOND == 1)
    dt = (nOS_Time)ticks;
#else
    dt = (nOS_Time)(ticks / NOS_CONFIG_TIME_TICKS_PER_SECOND);
    _prescaler += (uint16_t)(ticks % NOS_CONFIG_TIME_TICKS_PER_SECOND);
    if (_prescaler >= NOS_CONFIG_TIME_TICKS_PER_SECOND) {
        dt++;
        _prescaler -= NOS_CONFIG_TIME_TICKS_PER_SECOND;
    }
    if (dt > 0)
#endif
    {
        _time += dt;
#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
        nOS_WalkInList(&_event.waitList, _TickTime, NULL);
#endif
    }
    nOS_LeaveCritical(sr);
}

nOS_Time nOS_TimeGet (void)
{
    nOS_StatusReg   sr;
    nOS_Time        time;

    nOS_EnterCritical(sr);
    time = _time;
    nOS_LeaveCritical(sr);

    return time;
}

nOS_Error nOS_TimeSet (nOS_Time time)
{
    nOS_StatusReg   sr;

    nOS_EnterCritical(sr);
    _time = time;
#if (NOS_CONFIG_TIME_TICKS_PER_SECOND > 1)
    _prescaler = 0;
#endif
    nOS_LeaveCritical(sr);

    return NOS_OK;
}

nOS_TimeDate nOS_TimeConvert (nOS_Time time)
{
    nOS_TimeDate    timedate;
    uint16_t        days;

    /* First extract HH:MM:SS from _time */
    timedate.second = time % 60;
    time /= 60;
    timedate.minute = time % 60;
    time /= 60;
    timedate.hour = time % 24;
    time /= 24;
    /* At this point, time is now in number of days since 1st January 1970 */

    /* Second, get week day we are */
    /* 1st January 1970 was a Thursday (4th day or index 3) */
    /* weekday go from 1 (Monday) to 7 (Sunday) */
    timedate.weekday = ((time + 3) % 7) + 1;

    /* Third, find in which year we are */
    timedate.year = 1970;
    days = 365; /* 1970 is not a leap year */
    while (time >= days) {
        time -= days;
        timedate.year++;
        days = DAYS_PER_YEAR(timedate.year);
    }

    /* Fourth, find in which month of the present year we are */
    timedate.month = 1;
    days = 31;  /* January have 31 days */
    while (time >= days) {
        time -= days;
        timedate.month++;
        days = DAYS_PER_MONTH(timedate.month, timedate.year);
    }

    /* Last, we have in which day of month we are */
    timedate.day = (uint8_t)(time + 1);

    return timedate;
}

#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
nOS_Error nOS_TimeWait (nOS_Time time)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (nOS_isrNestingCounter > 0) {
        err = NOS_E_ISR;
    } else
 #if (NOS_CONFIG_SCHED_LOCK_ENABLE > 0)
    if (nOS_lockNestingCounter > 0) {
        /* Can't switch context when scheduler is locked */
        err = NOS_E_LOCKED;
    } else
 #endif
    if (nOS_runningThread == &nOS_idleHandle) {
        err = NOS_E_IDLE;
    } else
#endif
    {
        nOS_EnterCritical(sr);
        if (time < _time) {
            err = NOS_E_ELAPSED;
        }
        else if (time == _time) {
            err = NOS_OK;
        }
        else {
            nOS_runningThread->ext = (void*)&time;
            err = nOS_WaitForEvent(&_event,
                                   NOS_THREAD_WAITING_TIME
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0) || (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                                  ,NOS_WAIT_INFINITE
#endif
                                  );
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_TIME_WAIT_ENABLE */

bool nOS_TimeIsLeapYear(uint16_t year)
{
    return IS_LEAP_YEAR(year);
}

uint16_t nOS_TimeGetDaysPerYear(uint16_t year)
{
    return DAYS_PER_YEAR(year);
}

uint8_t nOS_TimeGetDaysPerMonth(uint8_t month, uint16_t year)
{
   return DAYS_PER_MONTH(month,year);
}

nOS_TimeDate nOS_TimeDateGet (void)
{
    return nOS_TimeConvert(nOS_TimeGet());
}

nOS_Error nOS_TimeDateSet (nOS_TimeDate timedate)
{
    return nOS_TimeSet(nOS_TimeDateConvert(timedate));
}

nOS_Time nOS_TimeDateConvert (nOS_TimeDate timedate)
{
    nOS_Time    time = 0;
    uint16_t    year;
    uint8_t     month;

    /* Increment time variable until we reach timedate given by user */

    /* Do not count on-going year */
    year = 1970;
    while (year < timedate.year) {
        time += (DAYS_PER_YEAR(year) * 86400UL);
        year++;
    }

    /* Do not count on-going month */
    month = 1;
    while (month < timedate.month) {
        time += (DAYS_PER_MONTH(month, timedate.year) * 86400UL);
        month++;
    }

    /* Do not count half day */
    time += ((timedate.day-1) * 86400UL); /* 86400 seconds per day */

    time += (timedate.hour * 3600UL);
    time += (timedate.minute * 60UL);
    time += timedate.second;

    return time;
}

#if (NOS_CONFIG_TIME_WAIT_ENABLE > 0)
nOS_Error nOS_TimeDateWait (nOS_TimeDate timedate)
{
    return nOS_TimeWait(nOS_TimeDateConvert(timedate));
}
#endif
#endif  /* NOS_CONFIG_TIME_ENABLE */

#ifdef __cplusplus
}
#endif
