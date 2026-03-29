# Coil Saturation Tester

Arduino firmware to detect if a coil in a boost converter circuit is entering the magnetic saturation stage and infer its inductance.

## Files

- `coil_saturation_tester_function.ino`: Main firmware with inductance inference and saturation detection logic.
- `emulator.py`: Python physics emulator that models a DCM boost converter with coil saturation.
- `arduino_mock.h` / `arduino_mock.cpp`: C++ mocks for the Arduino API.
- `main.cpp`: Test runner that wraps the Arduino code.
- `generate_graphs.py`: Script to run the test and generate diagnostic plots.

## Theory and Inference

The firmware uses the power balance equation for a boost converter operating in **Discontinuous Conduction Mode (DCM)** to infer the inductance of the coil.

In DCM, the input power $P$ can be expressed as:
$$P = \frac{1}{2} L \cdot I_{pk}^2 \cdot f$$

Where the peak current $I_{pk}$ is:
$$I_{pk} = \frac{V_{supply} \cdot D \cdot T}{L}$$

Substituting $I_{pk}$ into the power equation:
$$P = \frac{1}{2} L \cdot \left(\frac{V_{supply} \cdot D \cdot T}{L}\right)^2 \cdot f = \frac{V_{supply}^2 \cdot D^2 \cdot T}{2 L}$$

The firmware solves for $L$:
$$L = \frac{V_{supply}^2 \cdot D^2 \cdot T}{2 P}$$

By measuring the average input current ($I_{avg}$), it calculates input power $P = V_{supply} \cdot I_{avg}$.

### Saturation Detection

As the duty cycle increases, the peak current $I_{pk}$ grows. When the inductor's magnetic core begins to saturate, the inductance $L$ drops significantly. The firmware monitors the inferred inductance and detects saturation when it falls below a threshold (80% of its initial value).

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

The script will save results to `test_results.png`.

![Inferred Inductance vs Duty Cycle](test_results.png)
