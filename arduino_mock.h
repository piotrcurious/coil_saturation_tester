#ifndef ARDUINO_MOCK_H
#define ARDUINO_MOCK_H

#include <iostream>
#include <string>
#include <vector>

#define OUTPUT 1
#define INPUT 0
#define A0 0
#define A1 1

class MockSerial {
public:
    void begin(int baud) {}
    void print(const char* s) { std::cout << s; }
    void print(float f) { std::cout << f; }
    void print(double d) { std::cout << d; }
    void print(int i) { std::cout << i; }
    void println(const char* s) { std::cout << s << std::endl; }
    void println(float f) { std::cout << f << std::endl; }
    void println(double d) { std::cout << d << std::endl; }
    void println(int i) { std::cout << i << std::endl; }
};

extern MockSerial Serial;

void pinMode(int pin, int mode);
void analogWrite(int pin, int val);
int analogRead(int pin);
void delay(int ms);

#endif
