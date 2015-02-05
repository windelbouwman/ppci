
module stm32f4xx;

var RCC_Type* RCC;
var GPIO_Type* GPIOD;

type struct {
    int CR;
    int PLLCFGR;
    int CFGR;
    int CIR;
    int AHB1RSTR;
    int AHB2RSTR;
    int AHB3RSTR;
    int reserved0;
    int APB1RSTR;
    int APB2RSTR;
    int reserved1a, reserved1b;
    int AHB1ENR;
    int AHB2ENR;
    int AHB3ENR;
    int reserved2;
    int APB1ENR, APB2ENR;
} RCC_Type;

type struct {
    int ISER0;
    int ISER1;
} NVIC_Type;

type struct {
    int CTRL;
    int LOAD;
    int CURRENT;
    int CALIB;
} Systick_Type;

function void init()
{
    RCC = 0x40023800;
    GPIOD = 0x40020C00;
}
