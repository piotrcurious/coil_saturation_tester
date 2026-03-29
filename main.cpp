#include "arduino_mock.h"

// Define types missing in basic mock
typedef unsigned char byte;

// Forward declarations of Arduino functions since they are defined later in .ino
void testAndPrint();
void readVoltages();
void calcInput();
void calcOutput();
void printResults(int duty);
void checkSaturation(int duty);

// Include the .ino content
#include "coil_saturation_tester_function.ino"

int main() {
    setup();
    // Only run loop once as it contains the sweep
    loop();
    return 0;
}
