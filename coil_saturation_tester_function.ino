// Coil Saturation Measurement Instrument
// Advanced DCM Inference with Grid-Search Calibration

#define PWM_PIN 9
#define VOUT_PIN A0
#define VIN_PIN A1

// Hardware Constants
#define RIN 1.0       // Current sense resistor (Ohms)
#define R_DIV_TOTAL 10.0 // 9:1 Divider -> 10x factor
#define VREF 5.0      // ADC Reference voltage
#define SUPPLY_V 5.0  // Input supply voltage

// Estimated/Calibrated Parameters
float current_freq = 20000.0;
float v_diode = 0.7;
float r_series = 0.3;
float l_nominal = 500e-6;

// Measurements
float vout = 0;
float iin_avg = 0;
float inductance_calc = 500e-6;
float inductance_ema = 0;

struct CalPoint { float d; float f; float vo; float ii; };

// Forward declarations
void calibrateInstrument();
void runMeasurementSweep();
void performMeasurements();
void reportTelemetry(int duty);

#ifndef ARDUINO
extern void setPWMFrequency(long f);
#else
void setPWMFrequency(long f) {
  // Mock does popen with frequency. Real Arduino needs Timer registers.
}
#endif

void setup() {
  pinMode(PWM_PIN, OUTPUT);
  analogWrite(PWM_PIN, 0);
  Serial.begin(115200);
  Serial.println("--- Advanced Coil Measurement Instrument ---");
  calibrateInstrument();
}

void loop() {
  runMeasurementSweep();
  delay(10000);
}

void calibrateInstrument() {
    Serial.println("Calibrating losses and nominal inductance...");

    CalPoint pts[6];
    float d_vals[3] = {0.10, 0.14, 0.18};

    for(int i=0; i<3; i++) {
        setPWMFrequency(20000);
        current_freq = 20000.0;
        analogWrite(PWM_PIN, (int)(d_vals[i] * 255));
        delay(400);
        performMeasurements();
        pts[i*2] = {d_vals[i], 20000.0, vout, iin_avg};

        setPWMFrequency(40000);
        current_freq = 40000.0;
        analogWrite(PWM_PIN, (int)(d_vals[i] * 255));
        delay(400);
        performMeasurements();
        pts[i*2+1] = {d_vals[i], 40000.0, vout, iin_avg};
    }

    float best_vd = 0.7;
    float best_rs = 0.0;
    float min_err = 1e12;

    // Grid search for Vd and Rs
    // Search Vd from 0.4 to 1.0, Rs from 0 to 1.0
    for (int vd_i = 40; vd_i <= 100; vd_i += 5) {
        float vd = vd_i / 100.0;
        for (int rs_i = 0; rs_i <= 100; rs_i += 10) {
            float rs = rs_i / 100.0;
            float l[6];
            float sum_l = 0;
            bool valid = true;
            for(int i=0; i<6; i++) {
                float pg = pts[i].ii * SUPPLY_V;
                float pn = pg - (pts[i].ii * pts[i].ii * rs);
                if (pn < 0.005) { valid = false; break; }
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

            if (rel_err < min_err) {
                min_err = rel_err;
                best_vd = vd;
                best_rs = rs;
                l_nominal = avg_l;
            }
        }
    }

    v_diode = best_vd;
    r_series = best_rs;

    setPWMFrequency(20000);
    current_freq = 20000.0;

    Serial.print("CALIBRATED_VD:"); Serial.println(v_diode);
    Serial.print("CALIBRATED_RS:"); Serial.println(r_series);
    Serial.print("CALIBRATED_L_NOM:"); Serial.println(l_nominal * 1e6);
}

void runMeasurementSweep() {
   Serial.println("Starting Measurement Sweep...");
   inductance_ema = l_nominal;
   for (int duty = 20; duty <= 240; duty += 2) {
      analogWrite(PWM_PIN, duty);
      delay(80);
      performMeasurements();

      float D = (float)duty / 255.0;
      float T = 1.0 / current_freq;

      float pin_gross = iin_avg * SUPPLY_V;
      float pin_net = pin_gross - (iin_avg * iin_avg * r_series);

      if (pin_net > 0.01 && vout > (SUPPLY_V + 0.5)) {
          float boost_factor = (vout + v_diode) / (vout + v_diode - SUPPLY_V);
          float l_instant = (0.5 * SUPPLY_V * SUPPLY_V * D * D * T) / pin_net * boost_factor;

          if (l_instant > 0.01) l_instant = 0.01;

          inductance_ema = (l_instant * 0.4) + (inductance_ema * 0.6);
          inductance_calc = inductance_ema;
      }

      reportTelemetry(duty);
      if (iin_avg > 4.6) break;
   }
   analogWrite(PWM_PIN, 0);
}

void performMeasurements() {
   long sum_vout = 0, sum_vin = 0;
   const int oversample = 150;
   for (int i = 0; i < oversample; i++) {
     sum_vout += analogRead(VOUT_PIN);
     sum_vin += analogRead(VIN_PIN);
   }
   vout = ((float)sum_vout / oversample) * VREF / 1023.0 * R_DIV_TOTAL;
   iin_avg = ((float)sum_vin / oversample) * VREF / 1023.0 / RIN;
}

void reportTelemetry(int duty) {
   float d_pct = (float)duty * 100.0 / 255.0;
   float T = 1.0 / current_freq;
   float ipk = (SUPPLY_V * (d_pct/100.0) * T) / inductance_calc;

   Serial.print("D:"); Serial.print(d_pct, 1); Serial.print("% ");
   Serial.print("Vo:"); Serial.print(vout, 2); Serial.print("V ");
   Serial.print("Ii:"); Serial.print(iin_avg, 4); Serial.print("A ");
   Serial.print("Ip:"); Serial.print(ipk, 3); Serial.print("A ");
   Serial.print("Le:"); Serial.print(inductance_calc * 1.0e6, 2); Serial.println("uH");
}
