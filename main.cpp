#include "arduino_mock.h"

// Define types missing in basic mock
typedef unsigned char byte;

// Forward declarations
void testAndPrint();
void readVoltages();
void printResults(int duty);

// Include the .ino content
#include "coil_saturation_tester_function.ino"

int main() {
    setup();
    loop();
    return 0;
}
