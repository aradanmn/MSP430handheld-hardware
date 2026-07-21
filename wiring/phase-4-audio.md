# Phase 4 Hardware — LM386 Audio Amp + Speaker
*Added before Lesson 14*

## Parts to Order

| Part | Description | Source | ~Cost |
|------|-------------|--------|-------|
| LM386N-1 | Audio power amplifier, DIP-8 | DigiKey, Amazon | $1 |
| 8Ω 0.5W speaker | Small, fits on breadboard | Amazon | $2 |
| 250µF electrolytic cap | Output coupling (pin 5 to speaker) | Any | $0.50 |
| 10µF electrolytic cap | Input coupling (PWM → pin 3) | Any | $0.25 |
| 10Ω resistor | Series with speaker output | Any | $0.10 |
| 0.047µF cap + 1.2kΩ | Zobel network (optional, reduces noise) | Any | $0.25 |
| 9V battery + snap | Power for LM386 (can use 5V from USB too) | Any | $2 |

## Circuit

```
MSP430 P2.4 (PWM) ──── 10µF cap ──────── LM386 pin 3 (+input)
                                          LM386 pin 2 (−input) ── GND
                                          LM386 pin 6 (VS) ── 5–9V
                                          LM386 pin 4 (GND) ── GND
                                          LM386 pin 1,8 ── (leave open for 20× gain)
                                          LM386 pin 7 ── 10µF ── GND  (bypass)
                                          LM386 pin 5 (output) ── 250µF cap ── 10Ω ── Speaker (+)
                                                                                        Speaker (−) ── GND
```

## MSP430 Connection

| Signal | MSP430 Pin | Notes |
|--------|-----------|-------|
| PWM out | P2.4 | Timer A1 CCR2 — generates square wave tones |
| (no other connections) | | LM386 is purely an analog output stage |

## How It Works

The MSP430 generates a square wave on P2.4 using Timer A1 in up-mode. Changing the CCR period changes the frequency (pitch). The 10µF cap blocks DC before the LM386 input. The LM386 amplifies the signal ~20× and drives the speaker through the 250µF output coupling cap.

**Gain adjustment:** Connecting a 1.2kΩ + 10µF series between pins 1 and 8 increases gain to 200×. Start without it — the default 20× is usually plenty.

## Tone Frequency Formula

```
PWM period = SMCLK / (CCR0 + 1)
frequency  = SMCLK / (CCR0 + 1)

At 1 MHz SMCLK:
  A4 (440 Hz) → CCR0 = 1000000/440 - 1 = 2271
  C5 (523 Hz) → CCR0 = 1000000/523 - 1 = 1911
  Middle C (262 Hz) → CCR0 = 1000000/262 - 1 = 3816
```
