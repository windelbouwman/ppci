
#ifndef _CABLE_ZYNQ_H_
#define _CABLE_ZYNQ_H_

#include <stdint.h>
#include "cable_common.h"

jtag_cable_t *cable_zynq_get_driver(void);
int  cable_zynq_init();
int  cable_zynq_out(uint8_t value);
int  cable_zynq_inout(uint8_t value, uint8_t *inval);
void cable_zynq_wait();
int  cable_zynq_opt(int c, char *str);

void jtag_set(int tck, int trstn, int tdi, int tms);
int jtag_get();
void jtag_close();

#endif
