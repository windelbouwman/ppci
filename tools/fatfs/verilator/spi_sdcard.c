/*
 * Reset sequence:
 * - master sends CMD0.
 * - master sends CMD8 with check pattern and supported voltages.
 * - master sends CMD58 to read OCR.
 * - master sends ACMD41 until card is ready.
 * - master sends CMD58 to get CCS.
 *
 * The master can then set the block length and perform single block reads.
 *
 * Supported features:
 * - reset
 * - single block read
 * - crc validation
 * - set blocklen
 *
 * The SD spec
 * (http://users.ece.utexas.edu/~valvano/EE345M/SD_Physical_Layer_Spec.pdf)
 * has a habit of not using names for commands and bit fields etc.  So we have
 * things like CMD58, ACMD41 etc...
 */
#define _GNU_SOURCE
#include <assert.h>
#include <fcntl.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "spi_sdcard.h"

#define DATA_BUF_SIZE 1024

#define IN_IDLE_STATE (1 << 0)
#define ILLEGAL_COMMAND (1 << 2)
#define CARD_HIGH_CAPACITY (1 << 6)
#define DATA_START_TOKEN 0xfe

#ifdef DEBUG
#define debug printf
#else
static inline void __attribute__((format(printf,1,2)))
	no_printf(const char *fmt, ...)
{
}
#define debug no_printf
#endif

enum card_state {
	STATE_READING_COMMAND,
	STATE_RESPONSE,
};

struct spi_command {
	uint8_t command;
	uint8_t argument[4];
	uint8_t crc;
};

struct spi_sdcard {
	int fd;
	union {
		struct spi_command current_cmd;
		uint8_t cmd_buf[sizeof(struct spi_command)];
	};
	char data_buf[DATA_BUF_SIZE];
	unsigned int num_bytes_rx;
	unsigned int num_bytes_tx;
	enum card_state state;
	unsigned int reset_poll_count;
	bool next_cmd_is_acmd;
	size_t blocklen;
	size_t msg_len;
	int ncr_delay;
};

struct spi_sdcard *spi_sdcard_new(const char *path)
{
	struct spi_sdcard *card;

	card = calloc(1, sizeof(*card));
	assert(card != NULL);
	card->state = STATE_READING_COMMAND;
	card->ncr_delay = 1;

	card->fd = open(path, O_RDONLY);
	assert(card->fd >= 0);

	return card;
}

static inline bool command_is_complete(const struct spi_sdcard *sd)
{
	return sd->num_bytes_rx == sizeof(sd->current_cmd);
}

static void read_data(struct spi_sdcard *sd, uint8_t v)
{
	assert(sd->num_bytes_rx < DATA_BUF_SIZE + sizeof(sd->current_cmd));

	if (sd->num_bytes_rx == 0 && (v & 0x80))
		return;

	if (sd->num_bytes_rx < sizeof(sd->current_cmd))
		sd->cmd_buf[sd->num_bytes_rx] = v;
	else if (sd->num_bytes_rx >= sizeof(sd->current_cmd) &&
		 sd->state == STATE_READING_COMMAND)
		sd->data_buf[sd->num_bytes_rx] = v;

	sd->num_bytes_rx++;
}

static void process_new_command(struct spi_sdcard *sd)
{
	sd->state = STATE_RESPONSE;
}

static void set_next_state(struct spi_sdcard *sd)
{
	if (command_is_complete(sd)) {
		debug("+ received %sCMD%u\n", sd->next_cmd_is_acmd ? "A" : "",
		       sd->current_cmd.command & 0x3f);
		process_new_command(sd);
	}
}

void spi_sdcard_next_byte_to_slave(struct spi_sdcard *sd, uint8_t v)
{
	read_data(sd, v);
	set_next_state(sd);
}

static void finish_command(struct spi_sdcard *sd)
{
	sd->state = STATE_READING_COMMAND;
	sd->num_bytes_tx = 0;
	sd->num_bytes_rx = 0;
	sd->ncr_delay = 1;
}

struct r7 {
	uint8_t bytes[5];
};

static void do_cmd8(struct spi_sdcard *sd)
{
	struct r7 r7;

	/* r1 response. */
	r7.bytes[0] = 0;
	r7.bytes[1] = 2 << 4; /* Version 2. */
	r7.bytes[2] = 0;
	r7.bytes[3] = 1; /* Accept a single voltage. */
	r7.bytes[4] = sd->current_cmd.argument[3];

	memcpy(sd->data_buf, &r7, sizeof(r7));
}

static bool reset_complete(struct spi_sdcard *sd)
{
	return sd->reset_poll_count++ >= 14;
}

struct r3 {
	uint8_t bytes[5];
};

static void do_cmd58(struct spi_sdcard *sd)
{
	struct r3 r3;

	/* r1 response. */
	r3.bytes[0] = 0;
	r3.bytes[1] = CARD_HIGH_CAPACITY | (!!reset_complete(sd) << 7);
	r3.bytes[2] = 0xff; /* Accept lots of voltages. */
	r3.bytes[3] = 0xfe;
	r3.bytes[4] = 0xfd;

	memcpy(sd->data_buf, &r3, sizeof(r3));
}

enum sd_cmds {
	/* Normal commands. */
	GO_IDLE_STATE = 0,
	SEND_OP_COND = 1,
	SEND_IF_COND = 8,
	SEND_CSD = 9,
	SEND_CID = 10,
	SEND_STATUS = 13,
	SET_BLOCKLEN = 16,
	READ_SINGLE_BLOCK = 17,
	APP_CMD = 55,
	READ_OCR = 58,
	/* Application commands. */
	SD_SEND_OP_COND = 41,
};

static void do_set_blocklen(struct spi_sdcard *sd)
{
	uint32_t blocklen = (sd->current_cmd.argument[0] << 24) |
			    (sd->current_cmd.argument[1] << 16) |
			    (sd->current_cmd.argument[2] << 8) |
			    (sd->current_cmd.argument[3] << 0);

	assert(sd->blocklen < sizeof(sd->data_buf) - 16);
	debug("+ set blocklen=%u\n", blocklen);
	sd->blocklen = blocklen;
}

static void do_block_read(struct spi_sdcard *sd)
{
	uint32_t data_address = (sd->current_cmd.argument[0] << 24) |
				(sd->current_cmd.argument[1] << 16) |
				(sd->current_cmd.argument[2] << 8) |
				(sd->current_cmd.argument[3] << 0);
	ssize_t br;

	debug("+ read from %08x\n", data_address);

	sd->msg_len = 0;
	sd->data_buf[sd->msg_len++] = 0; /* r1 response. */
	sd->data_buf[sd->msg_len++] = DATA_START_TOKEN; /* data start token. */
	br = pread(sd->fd, sd->data_buf + sd->msg_len, sd->blocklen, data_address);
	assert(br == sd->blocklen);
	sd->msg_len += br;

	/* CRC16 */
	sd->data_buf[sd->msg_len++] = 0xde;
	sd->data_buf[sd->msg_len++] = 0xad;
}

static void do_cid_read(struct spi_sdcard *sd)
{
	int i;

	debug("+ read CID\n");

	sd->msg_len = 0;
	sd->data_buf[sd->msg_len++] = 0; /* r1 response. */
	sd->data_buf[sd->msg_len++] = DATA_START_TOKEN; /* data start token. */
	for (i = 0; i < 16; ++i)
		sd->data_buf[sd->msg_len++] = i + 1;
	sd->data_buf[sd->msg_len++] = 0xde;
	sd->data_buf[sd->msg_len++] = 0xad;
}

static void do_csd_read(struct spi_sdcard *sd)
{
	debug("+ read CSD\n");

	sd->msg_len = 0;
	sd->data_buf[sd->msg_len++] = 0; /* r1 response. */
	sd->data_buf[sd->msg_len++] = DATA_START_TOKEN; /* data start token. */

	sd->data_buf[sd->msg_len++] = 1 << 6; /* CSD structure. */
	sd->data_buf[sd->msg_len++] = 0; /* TAAC */
	sd->data_buf[sd->msg_len++] = 0; /* NSAC */
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;
	sd->data_buf[sd->msg_len++] = 0;

	sd->data_buf[sd->msg_len++] = 0xde;
	sd->data_buf[sd->msg_len++] = 0xad;
}

uint8_t spi_sdcard_next_byte_to_master(struct spi_sdcard *sd)
{
	uint8_t v = 0xff;

	if (sd->state == STATE_RESPONSE && sd->ncr_delay != 0) {
		v = 0xff;
	} else if (sd->state == STATE_RESPONSE && !sd->next_cmd_is_acmd) {
		switch (sd->current_cmd.command & 0x3f) {
		case GO_IDLE_STATE:
			sd->blocklen = 512;
			sd->reset_poll_count = 0;
			v = IN_IDLE_STATE;
			finish_command(sd);
			break;
		case SEND_OP_COND:
			v = reset_complete(sd) ? 0 : IN_IDLE_STATE;
			finish_command(sd);
			break;
		case SEND_IF_COND:
			/* CMD8 sends an R7 response. */
			do_cmd8(sd);
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sizeof(struct r7) - 1)
				finish_command(sd);
			break;
		case SEND_CSD:
			if (sd->num_bytes_tx == 0)
				do_csd_read(sd);
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sd->msg_len - 1)
				finish_command(sd);
			break;
		case SEND_CID:
			if (sd->num_bytes_tx == 0)
				do_cid_read(sd);
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sd->msg_len - 1)
				finish_command(sd);
			break;
		case SEND_STATUS:
			if (sd->num_bytes_tx == 0) {
				sd->msg_len = 2;
				sd->data_buf[0] = sd->data_buf[1] = 0;
			}
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sd->msg_len - 1)
				finish_command(sd);
			break;
		case SET_BLOCKLEN:
			do_set_blocklen(sd);
			v = 0;
			finish_command(sd);
			break;
		case READ_SINGLE_BLOCK:
			if (sd->num_bytes_tx == 0)
				do_block_read(sd);
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sd->msg_len - 1)
				finish_command(sd);
			break;
		case APP_CMD:
			v = 0x0;
			sd->next_cmd_is_acmd = true;
			finish_command(sd);
			break;
		case READ_OCR:
			/* CMD58 sends an R3 response. */
			do_cmd58(sd);
			v = sd->data_buf[sd->num_bytes_tx];
			if (sd->num_bytes_tx == sizeof(struct r3) - 1)
				finish_command(sd);
			break;
		default:
			v = ILLEGAL_COMMAND;
			finish_command(sd);
			break;
		}
	} else if (sd->state == STATE_RESPONSE && sd->next_cmd_is_acmd) {
		sd->next_cmd_is_acmd = false;

		switch (sd->current_cmd.command & 0x3f) {
		case SD_SEND_OP_COND:
			v = reset_complete(sd) ? 0 : IN_IDLE_STATE;
			finish_command(sd);
			break;
		default:
			v = ILLEGAL_COMMAND;
			finish_command(sd);
			break;
		}
	}

	if (sd->state == STATE_RESPONSE && sd->ncr_delay != 0) {
		--sd->ncr_delay;
	} else {
		sd->num_bytes_tx = sd->state == STATE_READING_COMMAND ? 0 :
			sd->num_bytes_tx + 1;
	}

	return v;
}
