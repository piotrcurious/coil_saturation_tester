
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
  // Perform the test and print the results
  testAndPrint();
}

// Function to perform the test and print the results
void testAndPrint() {
   sat = 0; // Reset saturation
   // Sweep the duty cycle from 0 to 255 in steps of 5
   for (int duty = 0; duty <= 255; duty += 5) {
      // Write the duty cycle to the PWM pin
      analogWrite(PWM_PIN, duty);

      // Wait for a short delay to let the circuit stabilize
      delay(100);

      // Read and convert the output and input voltages
      readVoltages();

      // Calculate the input current and power
      calcInput();

      // Calculate the output power and efficiency
      calcOutput();

      // Print the results to the serial monitor
      printResults(duty);

      // Check if the core is saturated and calculate its saturation level if so
      checkSaturation(duty);
    
      // Break out of the loop if saturated
      if (sat > 0) break;
    
   }

   // Print a message indicating that the test is finished and its final saturation level 
   Serial.println("The test is finished!");
   Serial.print("The final saturation level is ");
   Serial.print(sat);
   Serial.println("V");
}

// Function to read and convert the output and input voltages from the analog pins
void readVoltages() {
   // Average multiple readings to reduce noise
   long sum_vout = 0;
   long sum_vin = 0;
   const int num_readings = 10;

   for (int i = 0; i < num_readings; i++) {
     sum_vout += analogRead(VOUT_PIN);
     sum_vin += analogRead(VIN_PIN);
   }

   float avg_vout = (float)sum_vout / num_readings;
   float avg_vin = (float)sum_vin / num_readings;

   // Read the output voltage from the analog pin and convert it to volts
   vout = avg_vout * VREF / 1023.0 * (R1 + R2) / R2;

   // Read the input voltage from the analog pin and convert it to volts
   vin = avg_vin * VREF / 1023.0;
}

// Function to calculate the input current and power from the input voltage and resistor value
void calcInput() {
   // Calculate the input current from the input voltage and resistor value
   iin = vin / RIN;

   // Calculate the input power from the input voltage and current
   // Assuming input supply to boost is VREF for this calculation
   pin = VREF * iin;
}

// Function to calculate the output power and efficiency from the output and input power
void calcOutput() {
   // Calculate the output power from the output voltage and load resistance
   pout = vout * vout / (R1 + R2);

   // Calculate the efficiency from the output and input power
   if (pin > 0) {
     eff = pout / pin;
   } else {
     eff = 0;
   }
}

// Function to print the duty cycle, output voltage, input voltage, input current, efficiency and saturation level to the serial monitor
void printResults(int duty) {
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
   Serial.println("");
}

// Function to check if the efficiency drops below a certain threshold (e.g. 0.8) and calculate and print the saturation level if so
void checkSaturation(int duty) {
   // Check if the efficiency drops below a certain threshold (e.g. 0.8)
   // Ignore very low duty cycles where efficiency calculations might be unstable
   // Our emulator gives high efficiency because of simple model, let's adjust threshold to 0.7 or something based on trial
   if (duty > 50 && eff < 0.8) {
      // Calculate the saturation level from the duty cycle and input voltage
      // This is a simplified proxy for saturation index
      sat = duty * VREF / 255.0;

      // Print a message indicating that the core is saturated and its saturation level
      Serial.println("The core is saturated!");
      Serial.print("The saturation level is ");
      Serial.print(sat);
      Serial.println("V");
   }
}
