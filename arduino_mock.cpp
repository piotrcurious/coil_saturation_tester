#include "arduino_mock.h"
#include <iostream>
#include <cstdio>
#include <memory>
#include <array>
#include <map>

MockSerial Serial;

static int last_duty = 0;
static std::map<int, std::pair<int, int>> emulator_cache;

void pinMode(int pin, int mode) {
}

void analogWrite(int pin, int val) {
    last_duty = val;
}

int analogRead(int pin) {
    if (emulator_cache.find(last_duty) == emulator_cache.end()) {
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
            emulator_cache[last_duty] = {vin_read, vout_read};
        } else {
            return 0;
        }
    }

    auto readings = emulator_cache[last_duty];
    if (pin == A1) return readings.first;
    if (pin == A0) return readings.second;
    return 0;
}

void delay(int ms) {
    // Clear cache on delay since it implies time has passed/state might change?
    // Actually for our sweep, the duty cycle changes, so we don't really need a cache beyond one duty.
    // But let's keep it for multiple reads of same pins in one 'step'.
    emulator_cache.clear();
}
