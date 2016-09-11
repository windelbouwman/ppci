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
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/socket.h> 

#include "uart.h"

int create_pts(void)
{
  struct sockaddr_in addr;
  int ret;
  int jp_comm_m;
  int jp_comm;
 
  addr.sin_family = AF_INET;
  addr.sin_port = htons(4567);
  addr.sin_addr.s_addr = INADDR_ANY;
  memset(addr.sin_zero, '\0', sizeof(addr.sin_zero));

  jp_comm_m = socket(PF_INET, SOCK_STREAM, 0);
  if(jp_comm_m < 0)
  {
    fprintf(stderr, "Unable to create comm socket: %s\n", strerror(errno));
    return 0;
  }

  int yes = 1;
  if(setsockopt(jp_comm_m, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
    fprintf(stderr, "Unable to setsockopt on the socket: %s\n", strerror(errno));
    return 0;
  }

  if(bind(jp_comm_m, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
    fprintf(stderr, "Unable to bind the socket: %s\n", strerror(errno));
    return 0;
  }

  if(listen(jp_comm_m, 1) == -1) {
    fprintf(stderr, "Unable to listen: %s\n", strerror(errno));
    return 0;
  }

  //ret = fcntl(jp_comm_m, F_GETFL);
  //ret |= O_NONBLOCK;
  //fcntl(jp_comm_m, F_SETFL, ret);

  fprintf(stderr, "Listening on port %d\n", 4567);
  
  if((jp_comm = accept(jp_comm_m, NULL, NULL)) == -1) {
    if(errno == EAGAIN)
      return 0;

    fprintf(stderr, "Unable to accept connection: %s\n", strerror(errno));
    return 0;
  }
  ret = fcntl(jp_comm, F_GETFL);
  ret |= O_NONBLOCK;
  fcntl(jp_comm, F_SETFL, ret);
  close(jp_comm_m);

  printf("UART communication connected!\n"); 
  return(jp_comm);
}

