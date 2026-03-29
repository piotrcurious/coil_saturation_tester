#include "arduino_mock.h"
#include <iostream>
#include <cstdio>
#include <memory>
#include <array>

MockSerial Serial;

static int last_duty = 0;

void pinMode(int pin, int mode) {
    // std::cout << "[Mock] Pin Mode " << pin << " set to " << mode << std::endl;
}

void analogWrite(int pin, int val) {
    // std::cout << "[Mock] Analog Write Pin " << pin << " value " << val << std::endl;
    last_duty = val;
}

int analogRead(int pin) {
    // Call python emulator
    char command[100];
    sprintf(command, "python3 emulator.py %d", last_duty);

    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(command, "r"), pclose);
    if (!pipe) {
        return 0;
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }

    int vin_read, vout_read;
    if (sscanf(result.c_str(), "%d %d", &vin_read, &vout_read) == 2) {
        if (pin == A1) return vin_read;
        if (pin == A0) return vout_read;
    }
    return 0;
}

void delay(int ms) {
    // NOP for speed
}
