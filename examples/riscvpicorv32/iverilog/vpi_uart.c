/*
 * A simple VPI interface to a UART.  Creates a pseudo terminal that can be
 * connected to with a serial communication program like minicom.  Verilog
 * calls $uart_put() with an 8 bit value to write, and calls $uart_get with a
 * nine bit value.  If there is data then bit 8 is set and the data is in 7:0.
 */
#define _GNU_SOURCE

#include <assert.h>
#include <err.h>
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>

#include <vpi_user.h>
#include <sys/socket.h>
#include "uart.h"



static int uart_compiletf(char *user_data)
{
	return 0;
}

static int uart_get_calltf(char *user_data)
{
	vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;
	struct uart_data *data = (struct uart_data *)user_data;
	char ichar = 0;

	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);

	argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
	vpi_get_value(argh, &argval);

	argval.value.integer = 0;
	if (recv(data->fd, &ichar, 1, 0) == 1)
		argval.value.integer = (1 << 8) | ichar;

	vpi_put_value(argh, &argval, NULL, vpiNoDelay);

	vpi_free_object(args_iter);

	return 0;
}

static int uart_put_calltf(char *user_data)
{
	vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;
	struct uart_data *data = (struct uart_data *)user_data;
	char ichar;

	systfref = vpi_handle(vpiSysTfCall, NULL);
	args_iter = vpi_iterate(vpiArgument, systfref);

	argh = vpi_scan(args_iter);
	argval.format = vpiIntVal;
	vpi_get_value(argh, &argval);
	ichar = argval.value.integer;
	if(send(data->fd, &ichar, 1, 0) != 1)
		warn("failed to write data to uart");
	vpi_put_value(argh, &argval, NULL, vpiNoDelay);

	vpi_free_object(args_iter);

	return 0;
}

static void uart_register(void)
{
	s_vpi_systf_data get = {
		.type		= vpiSysTask,
		.tfname		= "$uart_get",
		.calltf		= uart_get_calltf,
		.compiletf	= uart_compiletf,
		.sizetf		= 0,
	};
	s_vpi_systf_data put = {
		.type		= vpiSysTask,
		.tfname		= "$uart_put",
		.calltf		= uart_put_calltf,
		.compiletf	= uart_compiletf,
		.sizetf		= 0,
	};
	struct uart_data *data = malloc(sizeof(*data));

	assert(data != NULL);

        #ifdef DBGUART
	data->fd = create_pts();
        #endif
	get.user_data = (char *)data;
	put.user_data = (char *)data;

	vpi_register_systf(&get);
	vpi_register_systf(&put);
}

void (*vlog_startup_routines[])(void) = {
        uart_register,
        NULL
};
