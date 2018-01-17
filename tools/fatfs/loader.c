/*----------------------------------------------------------------------*/
/* Foolproof FatFs sample project for AVR              (C)ChaN, 2013    */
/*----------------------------------------------------------------------*/

typedef unsigned int  uint32_t;  
typedef signed   int   int32_t; 
typedef unsigned short  uint16_t;  
typedef signed   short   int16_t; 
typedef unsigned char  uint8_t;
typedef signed char   int8_t; 
typedef unsigned char byte;

#include "ff.h"		/* Declarations of FatFs API */
#include "xprintf.h"

typedef struct uart{
unsigned int dr;
unsigned int sr;
unsigned int ack;
} UART;


UART* uart1 = (UART*)(0x20000000);
FATFS FatFsInst;		/* FatFs work area needed for each volume */
FIL Fil;			/* File object needed for each open file */

void putcmon(unsigned char c)
{
    uart1->dr = c;
}


int main (void)
{
    UINT bw;
    char str[80];
    FRESULT res;
    xdev_out(putcmon);
    xprintf("MMC/SD-Cardbootloader Demo, ");
    res=f_mount(&FatFsInst, "", 0);		/* Give a work area to the default drive */
    res=f_open(&Fil, "greets.txt", FA_READ);
    if ( res == FR_OK) {
       xprintf("reading from greets.txt:\n\r");
       f_gets(&str[0], 80, &Fil);	/* Write data to the file */
       xprintf("%s",str);
       f_close(&Fil);								/* Close the file */
    }
    xprintf("Bye.\n\r");
}



/*---------------------------------------------------------*/
/* User Provided RTC Function called by FatFs module       */

DWORD get_fattime (void)
{
	/* Returns current time packed into a DWORD variable */
	return	  ((DWORD)(2013 - 1980) << 25)	/* Year 2013 */
			| ((DWORD)7 << 21)				/* Month 7 */
			| ((DWORD)28 << 16)				/* Mday 28 */
			| ((DWORD)0 << 11)				/* Hour 0 */
			| ((DWORD)0 << 5)				/* Min 0 */
			| ((DWORD)0 >> 1);				/* Sec 0 */
}

