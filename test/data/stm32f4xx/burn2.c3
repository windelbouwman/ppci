/*

This file blinks a LED on the STM32F4 discovery board.

the board has 4 leds on PD12, PD13, PD14 and PD15

*/

module burn2;

import stm32f4xx;

function int add(int a, int b)
{
    return a + b;
}

function void init(int pin)
{
    if (pin < 12)
    {
        return;
    }

    if (pin > 15)
    {
        return;
    }

    var stm32f4xx.RCC_Type RCC;
    RCC = cast<stm32f4xx.RCC_Type>(0x40023800);

    // Enable the clock to port D:
    RCC->AHB1ENR = RCC->AHB1ENR | (1 << 3);
    // Memory mapped control registers:
    var stm32f4xx.GPIO_Type GPIOD;
    GPIOD = cast<stm32f4xx.GPIO_Type>(0x40020C00);

    // PD13 == output (01)
    GPIOD->MODER = (1 << (pin << 1));
    GPIOD->ODR = (1 << pin);
}


function void main()
{
    // Vary between 12 and 15:
    init(13);

    var int a;
    a = 0;
    while (a < 1000)
    {
        a = add(a, 1);
    }

    while(true) {}
}

