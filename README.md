# Coil Saturation Tester

Arduino firmware to detect if a coil in a boost converter circuit is entering the magnetic saturation stage and infer its inductance.

## Files

- `coil_saturation_tester_function.ino`: Main firmware with inductance inference and calibration-based saturation detection logic.
- `emulator.py`: Python physics emulator that models a DCM boost converter with a continuous soft-saturation model.
- `arduino_mock.h` / `arduino_mock.cpp`: C++ mocks for the Arduino API.
- `main.cpp`: Test runner that wraps the Arduino code.
- `generate_graphs.py`: Script to run the test and generate diagnostic plots comparing inferred and actual inductance.

## Theory and Inference

The firmware uses the power balance equation for a boost converter operating in **Discontinuous Conduction Mode (DCM)** to infer the inductance of the coil.

In DCM, the input power $P$ can be expressed as:
$$P = \frac{V_{supply}^2 \cdot D^2 \cdot T}{2 L}$$

The firmware solves for $L$:
$$L = \frac{V_{supply}^2 \cdot D^2 \cdot T}{2 P}$$

### Calibration and Detection

1. **Calibration Phase**: During the 10% to 20% duty cycle sweep, the firmware calculates a baseline "nominal" inductance. This is because peak currents are low in this range, ensuring the core is not yet saturated.
2. **Saturation Detection**: As the duty cycle increases further, the firmware continues to infer $L$. When the inferred $L$ drops below 75% of the calibrated nominal baseline, it signals that the core has entered saturation.
3. **Noise Immunity**: The firmware uses 100x oversampling (averaging) on analog reads to handle high-frequency switching noise and measurement jitter.

## Testing Environment

### Prerequisites

- `g++`
- `python3`
- `matplotlib`

### How to Run

1. **Compile the test binary:**
   ```bash
   g++ -o test_arduino main.cpp arduino_mock.cpp -I.
   ```

2. **Run the simulation and generate graphs:**
   ```bash
   python3 generate_graphs.py
   ```

The script will produce `test_results.png` which includes a comparison between the firmware's inferred inductance and the emulator's actual (simulated) inductance.

![Inductance Comparison](test_results.png)
