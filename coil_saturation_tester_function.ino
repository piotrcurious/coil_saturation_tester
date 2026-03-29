
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
float l_nominal_baseline = 0; // Baseline inductance calculated during calibration
float ipk_calc = 0; // Calculated peak inductor current

// Setup function
void setup() {
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);

  pinMode(VOUT_PIN, INPUT);
  pinMode(VIN_PIN, INPUT);

  Serial.begin(9600);
}

// Loop function
void loop() {
  testAndPrint();
}

// Function to perform the test and print the results
void testAndPrint() {
   saturation_idx = 0;
   l_nominal_baseline = 0;
   float l_sum = 0;
   int l_count = 0;

   // Sweep the duty cycle from 0 to 255 in steps of 5
   for (int duty = 5; duty <= 255; duty += 5) {
      analogWrite(PWM_PIN, duty);
      delay(100);

      readVoltages();
      iin_avg = vin / RIN;
      pin = iin_avg * SUPPLY_V;

      float D = (float)duty / 255.0;
      float T = 1.0 / FREQ;

      // DCM power balance: L = 0.5 * V^2 * D^2 * T / P
      if (pin > 0.001) {
          inductance = (0.5 * SUPPLY_V * SUPPLY_V * D * D * T) / pin;
          // Calculate peak current: Ipk = (Vin * D * T) / L
          ipk_calc = (SUPPLY_V * D * T) / inductance;
      } else {
          inductance = 0;
          ipk_calc = 0;
      }

      // Calibration Phase: 10% to 20% duty cycle where peak current is low
      if (duty >= 25 && duty <= 50) {
          l_sum += inductance;
          l_count++;
          if (duty == 50) l_nominal_baseline = l_sum / l_count;
      }

      printResults(duty);

      // SAFETY: Shutdown if peak current is too high (e.g., 5A in simulation)
      if (ipk_calc > 5.0) {
          Serial.print("SAFETY SHUTDOWN: Peak current "); Serial.print(ipk_calc); Serial.println("A exceeds limit!");
          break;
      }

      // Saturation detection logic
      if (l_nominal_baseline > 0 && inductance < (l_nominal_baseline * 0.75)) {
          saturation_idx = duty;
          Serial.print("Core saturation detected at duty "); Serial.print(duty); Serial.println("%!");
          Serial.print("Calibration L (nominal): "); Serial.print(l_nominal_baseline * 1.0e6); Serial.println(" uH");
          Serial.print("Current Inferred L: "); Serial.print(inductance * 1.0e6); Serial.println(" uH");
          Serial.print("Peak Current: "); Serial.print(ipk_calc); Serial.println(" A");
          break;
      }
   }

   analogWrite(PWM_PIN, 0); // Always turn off after test
   Serial.println("Test finished.");
}

// Function to read and convert the output and input voltages from the analog pins
void readVoltages() {
   long sum_vout = 0;
   long sum_vin = 0;
   const int num_readings = 100;

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
   Serial.print("Ipk: ");
   Serial.print(ipk_calc);
   Serial.print("A\t");
   Serial.print("InferredL: ");
   Serial.print(inductance * 1.0e6);
   Serial.println(" uH");
}
