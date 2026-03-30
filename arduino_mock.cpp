#include "arduino_mock.h"
#include <iostream>
#include <cstdio>
#include <memory>
#include <array>
#include <map>
#include <tuple>

MockSerial Serial;

static int last_duty = 0;
static long last_freq = 20000;
static std::map<std::pair<int, long>, std::tuple<int, int, float>> emulator_cache;

void pinMode(int pin, int mode) {
}

void analogWrite(int pin, int val) {
    if (pin == 9) {
        last_duty = val;
    }
}

void setPWMFrequency(long f) {
    last_freq = f;
}

int analogRead(int pin) {
    auto key = std::make_pair(last_duty, last_freq);
    if (emulator_cache.find(key) == emulator_cache.end()) {
        char command[128];
        sprintf(command, "python3 emulator.py %d %ld", last_duty, last_freq);

        std::array<char, 128> buffer;
        std::string result_str;
        FILE* pipe = popen(command, "r");
        if (!pipe) return 0;

        while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
            result_str += buffer.data();
        }
        pclose(pipe);

        int vin_read = 0, vout_read = 0;
        float actual_l = 0;
        if (sscanf(result_str.c_str(), "%d %d %f", &vin_read, &vout_read, &actual_l) >= 3) {
            emulator_cache[key] = std::make_tuple(vin_read, vout_read, actual_l);
            std::cout << "ActualL: " << actual_l << " uH" << std::endl;
        } else {
            return 0;
        }
    }

    auto tuple = emulator_cache[key];
    if (pin == A1) return std::get<0>(tuple);
    if (pin == A0) return std::get<1>(tuple);
    return 0;
}

void delay(int ms) {
}
