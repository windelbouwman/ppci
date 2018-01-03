#include "svdpi.h"
#include "Vsystem__Dpi.h"
#include "spi_sdcard.h"

extern void writespi(const svBitVecVal* data);
extern int initspi();
extern svBitVecVal readspi();

static struct spi_sdcard *sdcard;

int initspi(void)
{
  sdcard = spi_sdcard_new("card.bin");
}


void writespi(const svBitVecVal* data)
{
  unsigned char uchar;
  uchar = (unsigned char) (*data);
  spi_sdcard_next_byte_to_slave(sdcard, uchar);
}

svBitVecVal readspi()
{
  unsigned char uchar = 0;
  svBitVecVal bv = 0;
  uchar = spi_sdcard_next_byte_to_master(sdcard);
  bv = uchar;
  return(bv);
}
