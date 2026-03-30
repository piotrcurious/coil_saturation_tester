#include "arduino_mock.h"
#include <iostream>
#include <cstdio>
#include <memory>
#include <stdexcept>
#include <string>
#include <array>
#include <tuple>

// Forward declarations for .ino code
void setup();
void loop();

// Define these to satisfy linker for .ino functions if not defined in .ino
void runTestCycle();
void performMeasurements();
void reportTelemetry(int duty);

int main() {
    setup();
    // Simulate one loop (which contains the full sweep)
    loop();
    return 0;
}

// Wrapper for the .ino file inclusion
#include "coil_saturation_tester_function.ino"
