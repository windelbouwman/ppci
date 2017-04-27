
#if STILL_HAVE__BOTTLES
	#pragma message(BEER_ON_WALL ",")
	#pragma message(OF_BEER ",")
	#pragma message(TAKE_ONE_DOWN)
	
	#include "dec.h"         
	#if NO_MORE__BOTTLES
		#define DEC2_STR ""
		#define DEC_STR "No more"
	#endif	
	
	#if JUST_ONE__BOTTLE
		#define BOTTLES "bottle"
	#else
		#define BOTTLES "bottles"	
	#endif
	
	#pragma message(BEER_ON_WALL ".")
	#pragma message("")
#endif 
