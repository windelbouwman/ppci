# APB Event Unit

This event unit was developed as part of the PULPino project. It can be plugged
into an APB bus and manages the core. It controls the core 'start' signal
`fetch_enable`, listens to events and interrupts from peripherals and clock
gates the core when it is not active.

It supports 32 events and 32 interrupt lines. It is assumed that events and
interrupts are pulsed, i.e. only high for one cycle. The event unit thus saves
the events and interrupts it has seen in a buffer. After the buffer there is a
mask that allows to select the events and interrupts that we are interested in.
