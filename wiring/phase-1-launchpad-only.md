# Phase 1 Hardware — LaunchPad Only
*Used in Lessons 1–5*

No additional hardware required. Everything in Phase 1 uses the **MSP-EXP430G2 LaunchPad** as-is.

## What's on the LaunchPad

| Resource | Pin | Notes |
|----------|-----|-------|
| LED1 (Red) | P1.0 | Active HIGH — our main blink/feedback LED |
| LED2 (Green) | P1.6 | Active HIGH — shared with SPI MISO later; safe to use for now |
| Button S2 | P1.3 | Active LOW — onboard user button, internal pull-up required |
| USB UART | P1.1 (RX), P1.2 (TX) | Connected to backchannel UART via eZ-FET |
| VCC | 3.3V | Available on header pins |
| GND | GND | Multiple available |

## Wiring Diagram

```
MSP-EXP430G2 LaunchPad
┌─────────────────────────────┐
│  [USB to Mac]               │
│                             │
│  P1.0 ──── LED1 (Red)  ●   │
│  P1.6 ──── LED2 (Green) ●   │
│  P1.3 ──── [S2 Button]      │
│                             │
│  Nothing external needed.   │
└─────────────────────────────┘
```

## What You'll Build / Learn

By the end of Phase 1 you will have:
- A working build + flash workflow on your VM
- LED blink code (game-over flash, score indicator patterns)
- Button-press detection with debounce
- Reusable subroutine library (`delay_ms`, `led_set`)
- Precise 1 MHz and 8 MHz clock configuration

## Shopping List

Nothing to buy — just plug in the LaunchPad via USB.
