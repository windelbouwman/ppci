/* cable_sim.c - Simulation connection drivers for the Advanced JTAG Bridge
   Copyright (C) 2001 Marko Mlinar, markom@opencores.org
   Copyright (C) 2004 György Jeney, nog@sdf.lonestar.org


   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA. */



#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <stdint.h>
#include <sys/mman.h>

#include "cable_zynq.h"
#include "errcodes.h"

#define debug(...) if (getenv("ADV_DEBUG10")) fprintf(stderr, __VA_ARGS__ )

/* Only used in the vpi */
jtag_cable_t zynq_cable_driver = {
    .name              = "zynq",
    .inout_func        = cable_zynq_inout,
    .out_func          = cable_zynq_out,
    .init_func         = cable_zynq_init,
    .opt_func          = cable_zynq_opt,
    .bit_out_func      = cable_common_write_bit,
    .bit_inout_func    = cable_common_read_write_bit,
    .stream_out_func   = cable_common_write_stream,
    .stream_inout_func = cable_common_read_stream,
    .flush_func        = NULL,
    .opts              = "",
    .help              = "",
};


#define JTAG_EMU_AXI_ADDR   0x51020000

#define MAP_SIZE 4096UL
#define MAP_MASK (MAP_SIZE - 1)


int   mem_fd;
char* jtag_map;

char* jtag_base;

/*-----------------------------------------------[ ZYNQ specific functions ]---*/
jtag_cable_t *cable_zynq_get_driver(void)
{
  return &zynq_cable_driver;
}


int cable_zynq_init()
{
  int retval = APP_ERR_NONE;

  jtag_base = NULL;
  jtag_map = MAP_FAILED;
  mem_fd = -1;

  if ((mem_fd = open("/dev/mem", O_RDWR|O_SYNC) ) < 0) {
    printf("can't open /dev/mem \n");

    retval = APP_ERR_INIT_FAILED;
    goto fail;
  }

  jtag_map = (char*)mmap(
      NULL,
      MAP_SIZE,
      PROT_READ|PROT_WRITE,
      MAP_SHARED,
      mem_fd,
      JTAG_EMU_AXI_ADDR & ~MAP_MASK
      );


  if (jtag_map == MAP_FAILED) {
    perror("mmap error\n");

    retval = APP_ERR_INIT_FAILED;
    goto fail;
  }

  jtag_base = jtag_map + (JTAG_EMU_AXI_ADDR & MAP_MASK);

  // configure as input/output
  volatile uint32_t* dir = (volatile uint32_t*)(jtag_base + 0x4);
  *dir = 0x10;

  debug("ZYNQ cable ready!");

  return retval;

fail:
  jtag_close();

  return retval;
}

int cable_zynq_out(uint8_t value)
{
  int tck   = (value & 0x1) >> 0;
  int trstn = (value & 0x2) >> 1;
  int tdi   = (value & 0x4) >> 2;
  int tms   = (value & 0x8) >> 3;

  debug("Sent %d\n", value);
  jtag_set(tck, trstn, tdi, tms);

  return APP_ERR_NONE;
}

int cable_zynq_inout(uint8_t value, uint8_t *inval)
{
  uint8_t dat;

  dat = jtag_get();

  cable_zynq_out(value);

  *inval = dat;

  return APP_ERR_NONE;
}

int cable_zynq_opt(int c, char *str)
{
  return APP_ERR_NONE;
}

void jtag_set(int tck, int trstn, int tdi, int tms) {
  volatile uint32_t* out = (volatile uint32_t*)(jtag_base);

  // now we can actually write to the peripheral
  uint32_t val = 0x0;
  if (tck == 1)
    val |= (1 << 0);

  if (trstn)
    val |= (1 << 1);

  if (tdi)
    val |= (1 << 2);

  if (tms)
    val |= (1 << 3);

  *out  = val;
}

int jtag_get() {
  volatile uint32_t* in = (volatile uint32_t*)(jtag_base);

  uint32_t val = *in;

  val = (val >> 4) & 0x1;

  return val;
}

void jtag_close() {
  if (mem_fd != -1)
    close(mem_fd);

  if(jtag_map != MAP_FAILED)
    munmap(jtag_map, MAP_SIZE);
}
