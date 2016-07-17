#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <simavr/sim_avr.h>
#include <simavr/sim_hex.h>
#include <simavr/sim_irq.h>

void uart_in_hook(avr_irq_t* irq, uint32_t value, void*param)
{
  printf("%X\n", value);
}

#define IRQ_UART_COUNT 1
static const char * irq_names[IRQ_UART_COUNT] = {
  [0] = "8<uart_in"
};


avr_irq_t* irq;

void init_uart(avr_t* avr)
{
  irq = avr_alloc_irq(&avr->irq_pool, 0, IRQ_UART_COUNT, irq_names);
  avr_irq_register_notify(irq + 0, uart_in_hook, 0);
  avr_irq_t* src = avr_io_getirq(avr, AVR_IOCTL_UART_GETIRQ('0'), UART_IRQ_OUTPUT);
  avr_connect_irq(src, irq + 0);
}

int main(int argc, char* argv[])
{
  avr_t* avr;
  avr = avr_make_mcu_by_name("atmega328p");
  if (!avr) {
    fprintf(stderr, "Error making core\n");
    exit(1);
  }

  uint32_t boot_size, boot_base;
  char *bootpath = argv[1]; // "test.hex";

  uint8_t *boot = read_ihex_file(bootpath, &boot_size, &boot_base);
  if (!boot) {
    fprintf(stderr, "Error loading %s\n", bootpath);
    exit(1);
  }

  avr_init(avr);
  avr->frequency = 16000000;
  memcpy(avr->flash + boot_base, boot, boot_size);
  avr->pc = boot_base;
  avr->codeend = avr->flashend;
  avr->log = 1 + 2;


  int state = cpu_Running;
  while (!(state == cpu_Done || state == cpu_Crashed)) {
    state = avr_run(avr);
  }

  return 0;
}
