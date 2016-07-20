
#include "verilated.h"


int main(int argc, char **argv, char **env)
{
  Vour* top = new Vour;
  while (!Verilated::gotFinish())
  {
    top->eval();
  }

  exit(0);
}
