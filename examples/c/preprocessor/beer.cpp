
// 99 Bottles written entirely in Visual C++ preprocessor directives.
// By Wim Rijnders.
#pragma warning(disable : 4005 )

#define BOTTLES "bottles"
#define TAKE_ONE_DOWN "Take one down, pass it around,"
#define DEC_NUM 9
#define DEC_STR "9"
#define DEC2_NUM 9
#define DEC2_STR "9"

#define TEST_BOTTLES(a,b) (DEC2_NUM == a  && DEC_NUM == b )
#define STILL_HAVE__BOTTLES !TEST_BOTTLES(0,0)
#define NO_MORE__BOTTLES TEST_BOTTLES(0,0)
#define JUST_ONE__BOTTLE TEST_BOTTLES(0,1)

#define OF_BEER DEC2_STR DEC_STR " " BOTTLES " of beer"
#define BEER_ON_WALL OF_BEER " on the wall"

#include "sing.h"
