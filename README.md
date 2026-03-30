# Advanced Coil Measurement Instrument

Precision Arduino firmware to measure and track coil inductance across its full operating range, with automatic calibration for power losses and magnetic saturation detection.

## Key Features

- **Automated Loss Calibration**: Uses a dual-frequency (20kHz/40kHz), multi-point grid search to automatically solve for diode forward voltage ($V_d$) and series resistance ($R_s$).
- **Precision Inductance Inference**: Employs an advanced DCM power-balance model that accounts for $V_{in}$ and $V_{out}$ boost factors:
  $$L = \frac{V_{in}^2 \cdot D^2 \cdot T}{2 \cdot (P_{gross} - I_{in}^2 \cdot R_s)} \cdot \frac{V_{out} + V_d}{V_{out} + V_d - V_{in}}$$
- **Saturation Tracking**: Real-time tracking of effective inductance as a function of peak current ($I_{pk}$), allowing for the detection of core saturation.
- **Mock & Emulator Suite**: Includes a C++ Arduino hardware mock and a Python physics engine for high-fidelity offline verification.

## Project Structure

- `coil_saturation_tester_function.ino`: Core firmware logic (Arduino IDE compatible).
- `emulator.py`: Python physics engine modeling a DCM boost converter with soft-saturation (L vs. Ipk) and ADC noise.
- `arduino_mock.h / .cpp`: C++ framework to simulate the Arduino environment on a PC.
- `main.cpp`: Entry point for the simulated hardware environment.
- `generate_graphs.py`: Automated evaluation suite that runs the simulation and produces diagnostic dashboards.

## Calibration and Accuracy

The instrument performs an initial 6-point calibration sweep to minimize measurement variance. In simulations with realistic noise and losses, it achieves:
- **Parameter Recovery**: Successfully identifies diode voltage (e.g., $V_d \approx 1.0V$) and coil resistance.
- **Inductance Precision**: Maintains an average error of **<10%** compared to the actual instantaneous inductance across the full duty cycle range.
- **Robustness**: Uses up to 500x oversampling during calibration to filter out ADC noise.

## Getting Started

### Prerequisites

- `g++` (C++11 or higher)
- `python3`
- `matplotlib` and `numpy` (optional, for graphing)

### Evaluation Suite

To run the full simulation and generate the diagnostic dashboard:

```bash
# 1. Compile the hardware mock
g++ -O3 main.cpp arduino_mock.cpp -o arduino_app

# 2. Run the evaluation script
python3 generate_graphs.py
```

This will produce `test_results.png`, which contains:
1. **Output Voltage**: Measured vs. Ideal CCM boost curve.
2. **Peak Current**: Tracked peak current through the coil.
3. **Inductance Tracking**: Comparison of inferred effective $L$ vs. simulated actual $L$.
4. **Saturation Curve**: $L$ vs. $I_{pk}$ showing the magnetic saturation profile.
5. **Measurement Error %**: Relative error between inferred and actual values.
6. **Input Current**: Average current consumption.

![Diagnostic Dashboard](test_results.png)

## Hardware Implementation

- **PWM Pin (9)**: Drives the boost converter MOSFET.
- **Vout Pin (A0)**: Monitors output voltage via a 10x resistive divider.
- **Vin Pin (A1)**: Monitors average input current via a 1.0 Ohm sense resistor.
- **Supply Voltage**: 5.0V regulated input.
