
// Define the pins for the PWM and the analog input
#define PWM_PIN 9
#define ANALOG_PIN A0

// Define the parameters for the dc-dc converter
#define INPUT_VOLTAGE 5.0 // The voltage of the PWM signal in volts
#define OUTPUT_VOLTAGE 12.0 // The desired output voltage of the converter in volts
#define DUTY_CYCLE 0.5 // The duty cycle of the PWM signal (0 to 1)
#define SWITCHING_FREQUENCY 10000 // The switching frequency of the PWM signal in Hz
#define INDUCTANCE 0.001 // The inductance of the test coil in henries
#define RESISTANCE 10.0 // The resistance of the load in ohms

// Define the saturation point of the magnetic core
#define SATURATION_POINT 1.5 // The maximum magnetic flux density of the core in teslas

// Define some constants for calculations
#define PI 3.14159
#define PERMEABILITY 4 * PI * 1e-7 // The permeability of free space in henries per meter

// Initialize some variables for storing values
float output_voltage; // The measured output voltage of the converter in volts
float efficiency; // The estimated efficiency of the converter (0 to 1)
float flux_density; // The estimated magnetic flux density of the core in teslas
float capacity; // The estimated capacity of the core until saturation (0 to 1)

void setup() {
  // Set the PWM pin as output and the analog pin as input
  pinMode(PWM_PIN, OUTPUT);
  pinMode(ANALOG_PIN, INPUT);

  // Set the PWM frequency and duty cycle
  analogWriteFrequency(PWM_PIN, SWITCHING_FREQUENCY);
  analogWrite(PWM_PIN, DUTY_CYCLE * 255);
}

void loop() {
  // Read the output voltage from the analog pin and convert it to volts
  output_voltage = analogRead(ANALOG_PIN) * (5.0 / 1023.0) * (RESISTANCE + RESISTANCE) / RESISTANCE;

  // Estimate the efficiency of the converter using the input and output power
  efficiency = (output_voltage * output_voltage / RESISTANCE) / (INPUT_VOLTAGE * INPUT_VOLTAGE / RESISTANCE * DUTY_CYCLE);

  // Estimate the magnetic flux density of the core using the output voltage and the inductance
  flux_density = output_voltage / (2 * PI * SWITCHING_FREQUENCY * INDUCTANCE);

  // Estimate the capacity of the core until saturation using the flux density and the saturation point
  capacity = (SATURATION_POINT - flux_density) / SATURATION_POINT;

  // Check if the core is in saturation or not and print a message accordingly
  if (flux_density >= SATURATION_POINT) {
    Serial.println("The core is in saturation.");
  } else {
    Serial.println("The core is not in saturation.");
    Serial.print("The capacity until saturation is ");
    Serial.print(capacity * 100);
    Serial.println("%.");
  }

  // Print some other values for debugging purposes
  Serial.print("The output voltage is ");
  Serial.print(output_voltage);
  Serial.println(" V.");
  Serial.print("The efficiency is ");
  Serial.print(efficiency * 100);
  Serial.println("%.");
  Serial.print("The flux density is ");
  Serial.print(flux_density);
  Serial.println(" T.");

  // Wait for a second before repeating
  delay(1000);
}
