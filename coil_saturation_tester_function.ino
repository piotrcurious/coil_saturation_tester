
// Define the pins and constants
#define PWM_PIN 9 // PWM pin for the boost converter
#define VOUT_PIN A0 // Analog pin for the output voltage of the boost converter
#define VIN_PIN A1 // Analog pin for the input voltage of the boost converter
#define RIN 1.0 // Current shunt resistor in ohms
#define R1 1000 // Voltage divider resistor 1 value in ohms
#define R2 1000 // Voltage divider resistor 2 value in ohms
#define VREF 5.0 // Reference voltage in volts
#define SUPPLY_V 5.0 // Supply voltage to the boost converter
#define FREQ 100000.0 // Switching frequency in Hz

// Define some variables
float vout = 0; // Output voltage of the boost converter
float vin = 0; // Input voltage across RIN (shunt)
float iin_avg = 0; // Average input current
float pin = 0; // Input power
float inductance = 0; // Inferred inductance in Henry
float saturation_idx = 0; // Index for saturation detection

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
  // Perform the test and print the results
  testAndPrint();
}

// Function to perform the test and print the results
void testAndPrint() {
   saturation_idx = 0;
   float initial_inductance = 0;

   // Sweep the duty cycle from 0 to 255 in steps of 5
   for (int duty = 5; duty <= 255; duty += 5) {
      // Write the duty cycle to the PWM pin
      analogWrite(PWM_PIN, duty);

      // Wait for a short delay to let the circuit stabilize
      delay(100);

      // Read and convert the output and input voltages
      readVoltages();

      // Calculate input current and power
      iin_avg = vin / RIN;
      pin = iin_avg * SUPPLY_V;

      // Infer inductance L from DCM power balance
      float D = (float)duty / 255.0;
      float T = 1.0 / FREQ;

      if (pin > 0.0) {
          inductance = (0.5 * SUPPLY_V * SUPPLY_V * D * D * T) / pin;
      } else {
          inductance = 0;
      }

      // Print the results to the serial monitor
      printResults(duty);

      // Logic to pick a stable initial inductance
      if (duty == 10) initial_inductance = inductance;

      // Saturation detection
      if (duty > 15 && initial_inductance > 0 && inductance < (initial_inductance * 0.8)) {
          saturation_idx = duty;
          Serial.println("Core saturation detected!");
          Serial.print("Initial L: "); Serial.print(initial_inductance * 1.0e6); Serial.println(" uH");
          Serial.print("Current L: "); Serial.print(inductance * 1.0e6); Serial.println(" uH");
          break;
      }
   }

   // Print a message indicating that the test is finished
   Serial.println("Test finished.");
}

// Function to read and convert the output and input voltages from the analog pins
void readVoltages() {
   long sum_vout = 0;
   long sum_vin = 0;
   const int num_readings = 50;

   for (int i = 0; i < num_readings; i++) {
     sum_vout += analogRead(VOUT_PIN);
     sum_vin += analogRead(VIN_PIN);
   }

   float avg_vout = (float)sum_vout / num_readings;
   float avg_vin = (float)sum_vin / num_readings;

   vout = avg_vout * VREF / 1023.0 * (R1 + R2) / R2;
   vin = avg_vin * VREF / 1023.0;
}

// Function to print results
void printResults(int duty) {
   Serial.print("Duty cycle: ");
   Serial.print(duty);
   Serial.print("%\t");
   Serial.print("Vout: ");
   Serial.print(vout);
   Serial.print("V\t");
   Serial.print("Iin_avg: ");
   Serial.print(iin_avg);
   Serial.print("A\t");
   Serial.print("Inferred L: ");
   Serial.print(inductance * 1.0e6); // Show in uH
   Serial.println(" uH");
}
