#ifndef __SPI_SDCARD_H__
#define __SPI_SDCARD_H__

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

struct spi_sdcard;

struct spi_sdcard *spi_sdcard_new(const char *path);

uint8_t spi_sdcard_next_byte_to_master(struct spi_sdcard *sd);
void spi_sdcard_next_byte_to_slave(struct spi_sdcard *sd, uint8_t v);

#ifdef __cplusplus
};
#endif

#endif /* __SPI_SDCARD_H__ */
