/*

This file blinks a LED on the STM32F4 discovery board.

the board has 4 leds on PD12, PD13, PD14 and PD15

*/

module burn2;

import stm32f4xx;
import bsp;
import io;

function int add(int a, int b)
{
    return a + b;
}

var int x;
var int value;

function void init(int pin)
{
    x = 12;
    value = 0;
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
    GPIOD->MODER = GPIOD->MODER | (1 << (pin << 1));
    GPIOD->ODR = GPIOD->ODR | (1 << pin);
}

function void systick()
{
    var stm32f4xx.GPIO_Type GPIOD;
    GPIOD = cast<stm32f4xx.GPIO_Type>(0x40020C00);

    x = x + 1;
    if (x > 15)
    {
        x = 12;

        if (value == 0)
        {
            value = 1;
        }
        else
        {
            value = 0;
        }
    }

    if (value == 0)
    {
        GPIOD->BSRR = (1 << (x + 16));
    }
    else
    {
        GPIOD->BSRR = (1 << (x));
    }

    // Test itm trace:
    bsp.putc(65); // Send out 'A'
    io.print2("Value = ", value);
}


function void main()
{
    // Vary between 12 and 15:
    init(15);
    init(14);
    init(13);

    // Enable systick:
    var stm32f4xx.NVIC_Type nvic;
    nvic = cast<stm32f4xx.NVIC_Type>(0xE000E100);
    nvic->ISER0 = (1 << 15)

    // Systick control register ( cortex TRM )
    var stm32f4xx.Systick_Type Systick;
    Systick  = cast<stm32f4xx.Systick_Type>(0xE000E010);
    Systick->LOAD = 1875000;
    Systick->CTRL = 0x3;

    init(12);

    while(true)
    {
    }
}

