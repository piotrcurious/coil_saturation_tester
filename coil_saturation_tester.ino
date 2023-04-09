
// Define the pins and constants
#define PWM_PIN 9 // PWM pin for the boost converter
#define VOUT_PIN A0 // Analog pin for the output voltage of the boost converter
#define VIN_PIN A1 // Analog pin for the input voltage of the boost converter
#define RIN 10 // Input resistor value in ohms
#define R1 1000 // Voltage divider resistor 1 value in ohms
#define R2 1000 // Voltage divider resistor 2 value in ohms
#define VREF 5.0 // Reference voltage in volts

// Define some variables
float vout = 0; // Output voltage of the boost converter
float vin = 0; // Input voltage of the boost converter
float iin = 0; // Input current of the boost converter
float pout = 0; // Output power of the boost converter
float pin = 0; // Input power of the boost converter
float eff = 0; // Efficiency of the boost converter
float sat = 0; // Saturation level of the magnetic core

// Setup function
void setup() {
  // Set the PWM pin as output and initialize it to zero duty cycle
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);

  // Set the analog pins as input
  pinMode(VOUT_PIN, INPUT);
  pinMode(VIN_PIN, INPUT);

  // Start serial communication at 9600 baud rate
  Serial.begin(9600);
}

// Loop function
void loop() {
  // Sweep the duty cycle from 0 to 255 in steps of 5
  for (int duty = 0; duty <= 255; duty += 5) {
    // Write the duty cycle to the PWM pin
    analogWrite(PWM_PIN, duty);

    // Wait for a short delay to let the circuit stabilize
    delay(100);

    // Read the output voltage from the analog pin and convert it to volts
    vout = analogRead(VOUT_PIN) * VREF / 1023.0 * (R1 + R2) / R2;

    // Read the input voltage from the analog pin and convert it to volts
    vin = analogRead(VIN_PIN) * VREF / 1023.0;

    // Calculate the input current from the input voltage and resistor value
    iin = vin / RIN;

    // Calculate the output power from the output voltage and load resistance
    pout = vout * vout / (R1 + R2);

    // Calculate the input power from the input voltage and current
    pin = vin * iin;

    // Calculate the efficiency from the output and input power
    eff = pout / pin;

    // Print the duty cycle, output voltage, input voltage, input current, efficiency and saturation level to the serial monitor
    Serial.print("Duty cycle: ");
    Serial.print(duty);
    Serial.print("%\t");
    Serial.print("Vout: ");
    Serial.print(vout);
    Serial.print("V\t");
    Serial.print("Vin: ");
    Serial.print(vin);
    Serial.print("V\t");
    Serial.print("Iin: ");
    Serial.print(iin);
    Serial.print("A\t");
    Serial.print("Efficiency: ");
    Serial.print(eff);
    Serial.println("%");

    // Check if the efficiency drops below a certain threshold (e.g. 80%)
    if (eff < 0.8) {
      // Calculate the saturation level from the duty cycle and input voltage
      sat = duty * vin / 255.0;

      // Print a message indicating that the core is saturated and its saturation level
      Serial.println("The core is saturated!");
      Serial.print("The saturation level is ");
      Serial.print(sat);
      Serial.println("V");

      // Break out of the loop
      break;
    }
  }
}
