#include "arduino_mock.h"
#include <iostream>
#include <cstdio>
#include <memory>
#include <array>
#include <map>
#include <tuple>

MockSerial Serial;

static int last_duty = 0;
static std::map<int, std::tuple<int, int, float>> emulator_cache;

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
        float actual_l;
        if (sscanf(result.c_str(), "%d %d %f", &vin_read, &vout_read, &actual_l) == 3) {
            emulator_cache[last_duty] = std::make_tuple(vin_read, vout_read, actual_l);
            std::cout << "ActualL: " << actual_l << " uH" << std::endl;
        } else {
            return 0;
        }
    }

    auto tuple = emulator_cache[last_duty];
    if (pin == A1) return std::get<0>(tuple);
    if (pin == A0) return std::get<1>(tuple);
    return 0;
}

void delay(int ms) {
    emulator_cache.clear();
}
