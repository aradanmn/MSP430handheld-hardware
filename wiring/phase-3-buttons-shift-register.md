# Phase 3 Hardware — 8-Button Input via SN74HC165N
*Added before Lesson 11*

## Parts to Order

| Part | Description | Source | ~Cost |
|------|-------------|--------|-------|
| SN74HC165N | 8-bit parallel-in serial-out shift register, DIP-16 | DigiKey, Mouser, Amazon | $1 |
| 6mm tactile buttons | Momentary push buttons, 4-pin | Amazon (pack of 20) | $3 |
| 10kΩ resistors | 1/4W — one per button for pull-up | Any | $1 |
| 0.1µF cap | Bypass cap for IC VCC | Any | $0.50 |

## Button Layout (Game Boy Style)

```
┌─────────────────────────────┐
│   [↑]                       │
│ [←][→]  [SEL][STA]  [B][A] │
│   [↓]                       │
└─────────────────────────────┘

Shift register bit mapping:
  Bit 7 = Up      (165 pin A)
  Bit 6 = Down    (165 pin B)
  Bit 5 = Left    (165 pin C)
  Bit 4 = Right   (165 pin D)
  Bit 3 = Select  (165 pin E)
  Bit 2 = Start   (165 pin F)
  Bit 1 = B       (165 pin G)
  Bit 0 = A       (165 pin H)
```

## SN74HC165N Pin Connections

| 74HC165 Pin | Name | Connect To |
|-------------|------|-----------|
| 1 | SH/LD (latch) | P2.3 (GPIO) |
| 2 | CLK | P1.5 (shared SPI CLK) |
| 10 | CLK INH | GND (always enabled) |
| 9 | QH (serial out) | P1.6 (USCI_B0 SOMI/MISO) |
| 15 | SER | GND (no daisy-chain) |
| 16 | VCC | 3.3V |
| 8 | GND | GND |
| A–H (3–6, 11–14) | Parallel inputs | One button each |

## Button Wiring (each of 8 buttons)

```
3.3V ─── 10kΩ ─── 165-pin-X ─── Button ─── GND

When button pressed: pin reads LOW (active low)
Bit in shift register reads 0 = pressed, 1 = released
```

## Reading Buttons in Code (Preview)

```asm
; Pulse SH/LD low to latch all 8 button states
bic.b   #BIT3, &P2OUT   ; PL low — latch
nop
nop
bis.b   #BIT3, &P2OUT   ; PL high — shift mode

; SPI read: send a dummy byte, receive button state
mov.b   #0xFF, &UCB0TXBUF
wait:   bit.b   #UCB0RXIFG, &IFG2
        jz      wait
mov.b   &UCB0RXBUF, R12  ; R12 = button bits (0=pressed)
xor.b   #0xFF, R12       ; invert: 1=pressed
```

## Important Note on Shared SPI

The OLED (Phase 2) and the SN74HC165N both share the SPI clock (P1.5) and MOSI (P1.7). They are separated by their chip-select lines:
- OLED CS → P2.0 (active LOW)
- 74HC165 SH/LD → P2.3

Only one should be active at a time. The code manages this automatically.
