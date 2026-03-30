// Precision Coil Measurement Instrument Firmware
// Optimized for Serial Communication with PC GUI

#define PWM_PIN 9
#define VOUT_PIN A0
#define VIN_PIN A1

// Hardware Constants
#define RIN 1.0       // Current sense resistor (Ohms)
#define R_DIV_TOTAL 10.0 // 9:1 Divider -> 10x factor
#define VREF 5.0      // ADC Reference voltage
#define SUPPLY_V 5.0  // Input supply voltage

// Calibrated Parameters
float current_freq = 20000.0;
float v_diode = 0.7;
float r_series = 0.0;
float l_nominal = 500e-6;

bool is_running = false;

struct CalPoint { float d; float f; float vo; float ii; };

// Forward declarations
void calibrateInstrument();
void runMeasurementSweep();
void performMeasurements(int oversample, float &vo, float &ii);
void setPWMFrequency(long f);

void setup() {
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);
  Serial.begin(115200);
  // Wait for command from PC
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'C') {
      calibrateInstrument();
    } else if (cmd == 'S') {
      is_running = true;
      runMeasurementSweep();
      is_running = false;
    } else if (cmd == 'H') {
      is_running = false;
      analogWrite(PWM_PIN, 0);
      Serial.println("STATUS:HALTED");
    }
  }
}

void setPWMFrequency(long f) {
  current_freq = (float)f;
#ifdef ARDUINO
  // Configure Timer 1 for Phase-Correct PWM at frequency 'f' (Hz) on Pins 9, 10
  // Formula: F_pwm = 16MHz / (2 * prescaler * TOP)
  // TOP = 16MHz / (2 * 1 * f) for prescaler=1
  unsigned int top = 8000000L / f;

  TCCR1A = _BV(COM1A1) | _BV(WGM11); // Phase Correct PWM, Clear OC1A on Compare Match
  TCCR1B = _BV(WGM13) | _BV(CS10);    // Mode 10 (PWM, Phase Correct, TOP=ICR1), Prescaler=1
  ICR1 = top;
#endif
}

void calibrateInstrument() {
    Serial.println("STATUS:CALIBRATING");

    CalPoint pts[6];
    float d_vals[3] = {0.15, 0.22, 0.30};

    for(int i=0; i<3; i++) {
        setPWMFrequency(20000);
        analogWrite(PWM_PIN, (int)(d_vals[i] * 255));
        delay(400);
        performMeasurements(400, pts[i*2].vo, pts[i*2].ii);
        pts[i*2].d = d_vals[i];
        pts[i*2].f = 20000.0;

        setPWMFrequency(40000);
        analogWrite(PWM_PIN, (int)(d_vals[i] * 255));
        delay(400);
        performMeasurements(400, pts[i*2+1].vo, pts[i*2+1].ii);
        pts[i*2+1].d = d_vals[i];
        pts[i*2+1].f = 40000.0;
    }

    float best_vd = 0.7, best_rs = 0.0, min_err = 1e12;

    for (int vd_i = 40; vd_i <= 110; vd_i += 5) {
        float vd = vd_i / 100.0;
        for (int rs_i = 0; rs_i <= 100; rs_i += 5) {
            float rs = rs_i / 100.0;
            float l[6];
            float sum_l = 0;
            bool valid = true;
            for(int i=0; i<6; i++) {
                float pg = pts[i].ii * SUPPLY_V;
                float pn = pg - (pts[i].ii * pts[i].ii * rs);
                if (pn < 0.01) { valid = false; break; }
                float boost = (pts[i].vo + vd) / (pts[i].vo + vd - SUPPLY_V);
                if (boost < 1.0) { valid = false; break; }
                l[i] = (0.5 * SUPPLY_V * SUPPLY_V * pts[i].d * pts[i].d * (1.0/pts[i].f)) / pn * boost;
                sum_l += l[i];
            }
            if (!valid) continue;
            float avg_l = sum_l / 6.0;
            float err_sum = 0;
            for(int i=0; i<6; i++) err_sum += (l[i] - avg_l) * (l[i] - avg_l);
            float rel_err = sqrt(err_sum / 6.0) / avg_l;
            float penalty = 1.0 + (rs * 0.05) + (abs(vd - 0.7) * 0.05);
            if (rel_err * penalty < min_err) {
                min_err = rel_err * penalty;
                best_vd = vd; best_rs = rs; l_nominal = avg_l;
            }
        }
    }
    v_diode = best_vd; r_series = best_rs;
    setPWMFrequency(20000);
    analogWrite(PWM_PIN, 0);

    Serial.print("RESULT:VD="); Serial.println(v_diode, 2);
    Serial.print("RESULT:RS="); Serial.println(r_series, 2);
    Serial.print("RESULT:LNOM="); Serial.println(l_nominal * 1e6, 2);
    Serial.println("STATUS:READY");
}

void runMeasurementSweep() {
   Serial.println("STATUS:SWEEPING");
   Serial.println("DATA_HEADER:DUTY_PCT,VOUT,IIN,IPK,LEFF_UH");

   float l_ema = l_nominal;
   for (int duty = 20; duty <= 240; duty += 2) {
      if (Serial.available() > 0) {
        char cmd = Serial.read();
        if (cmd == 'H') {
          is_running = false;
          break;
        }
      }
      if (!is_running) break;
      analogWrite(PWM_PIN, duty);
      delay(50);
      float vo, ii;
      performMeasurements(150, vo, ii);

      float D = (float)duty / 255.0;
      float T = 1.0 / current_freq;
      float pin_net = (ii * SUPPLY_V) - (ii * ii * r_series);

      if (pin_net > 0.01 && vo > (SUPPLY_V + 0.5)) {
          float boost = (vo + v_diode) / (vo + v_diode - SUPPLY_V);
          float l_inst = (0.5 * SUPPLY_V * SUPPLY_V * D * D * T) / pin_net * boost;
          if (l_inst > 0.01) l_inst = 0.01;
          l_ema = (l_inst * 0.4) + (l_ema * 0.6);
      }

      float ipk = (SUPPLY_V * D * T) / l_ema;

      // DATA:23.5,12.4,0.05,0.12,480.5
      Serial.print("DATA:");
      Serial.print(D*100.0, 1); Serial.print(",");
      Serial.print(vo, 2); Serial.print(",");
      Serial.print(ii, 4); Serial.print(",");
      Serial.print(ipk, 3); Serial.print(",");
      Serial.println(l_ema * 1.0e6, 2);

      if (ii > 4.5) break; // Hard limit
   }
   analogWrite(PWM_PIN, 0);
   Serial.println("STATUS:READY");
}

void performMeasurements(int oversample, float &vo, float &ii) {
   long sum_vout = 0, sum_vin = 0;
   for (int i = 0; i < oversample; i++) {
     sum_vout += analogRead(VOUT_PIN);
     sum_vin += analogRead(VIN_PIN);
   }
   vo = ((float)sum_vout / oversample) * VREF / 1023.0 * R_DIV_TOTAL;
   ii = ((float)sum_vin / oversample) * VREF / 1023.0 / RIN;
}
