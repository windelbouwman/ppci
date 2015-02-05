/*

This file blinks a LED on the STM32F4 discovery board.

the board has 4 leds on PD12, PD13, PD14 and PD15

*/

module snake;

import stm32f4xx;
import arch;
import io;

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


    // Enable the clock to port D:
    stm32f4xx.RCC->AHB1ENR |= (1 << 3);

    // Memory mapped control registers:

    // PD13 == output (01)
    stm32f4xx.GPIOD->MODER |= (1 << (pin << 1));
    stm32f4xx.GPIOD->ODR |= (1 << pin);
}

function void systick()
{

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
        stm32f4xx.GPIOD->BSRR = (1 << (x + 16));
    }
    else
    {
        stm32f4xx.GPIOD->BSRR = (1 << (x));
    }

    // Test itm trace:
    arch.putc(65); // Send out 'A'
    io.print2("Value = ", value);
}


function void main()
{
    stm32f4xx.init();

    // Vary between 12 and 15:
    init(15);
    init(14);
    init(13);

    // Enable systick:
    var stm32f4xx.NVIC_Type* nvic;
    nvic = 0xE000E100;
    nvic->ISER0 = (1 << 15)

    // Systick control register ( cortex TRM )
    var stm32f4xx.Systick_Type* Systick;
    Systick  = 0xE000E010;
    Systick->LOAD = 1875000;
    Systick->CTRL = 0x3;

    init(12);

    while(true)
    {
    }
}

