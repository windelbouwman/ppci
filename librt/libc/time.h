
#ifndef TIME_H
#define TIME_H

#include <stdlib.h>

// TODO: this is a weird hack to prevent clashes with /usr/include/bits/types/time_t.h
#ifndef __time_t_defined
typedef int time_t;
#define __time_t_defined 1
#endif

// TODO: this is a weird hack to prevent clashes with /usr/include/bits/types/clock_t.h
// TBD: what would be an effective strategy?
#ifndef __clock_t_defined
typedef int clock_t;
#define __clock_t_defined 1
#endif

struct tm {
    int tm_sec;
    int tm_min;
    int tm_hour;
    int tm_mday;
    int tm_mon;
    int tm_year;
    int tm_wday;
    int tm_yday;
    int tm_isdst;
};

clock_t clock();

time_t time(time_t* timer);
double difftime(time_t end, time_t beginning);
char* ctime(const time_t * timer);
char* ctime_r(const time_t * timer, char*);

time_t mktime(struct tm* timeptr);
struct tm* gmtime(const time_t *timer);
struct tm* gmtime_r(const time_t *timer, struct tm* result);
struct tm* localtime(const time_t *timer);
struct tm* localtime_r(const time_t *timer, struct tm* result);

size_t strftime(char* ptr, size_t maxsize, const char* format, const struct tm* timeptr);
char* asctime(const struct tm * timeptr);
char* asctime_r(const struct tm * timeptr, char* buf);


#endif
