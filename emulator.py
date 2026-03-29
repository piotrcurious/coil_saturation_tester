import sys
import random
import math

def simulate(duty, noise=0.01):
    V_in = 5.0
    f = 100000.0
    T = 1.0 / f
    R_load = 2000.0
    L_nominal = 1.0e-3
    I_sat_threshold = 0.05
    VREF = 5.0
    RIN = 1.0

    D = duty / 255.0
    if D < 0.01: return 0, int((V_in/2.0/VREF)*1023), L_nominal

    t_on = D * T

    L = L_nominal
    for _ in range(5):
        I_pk = (V_in * t_on) / L
        L = L_nominal / (1.0 + (I_pk / I_sat_threshold)**4)

    if L < L_nominal * 0.1: L = L_nominal * 0.1

    # Power delivered in DCM: P = 0.5 * L * I_pk^2 * f
    P_in = 0.5 * L * (I_pk**2) * f

    # Simple efficiency model: eff = 0.95 - (I_pk^2 * resistance_factor)
    eff = 0.95 - (I_pk**2 * 0.05)
    if eff < 0.1: eff = 0.1

    # SCALE for visibility on 10-bit ADC
    scale = 200.0
    P_in_scaled = P_in * scale
    I_in_avg = P_in_scaled / V_in

    vin_measured = I_in_avg * RIN
    V_out = math.sqrt(P_in_scaled * eff * R_load)
    if V_out < V_in: V_out = V_in
    vout_measured = V_out / 2.0

    # Noise
    vin_measured += (random.random() - 0.5) * noise
    vout_measured += (random.random() - 0.5) * noise * 2.0

    read_vin = int((vin_measured / VREF) * 1023)
    read_vout = int((vout_measured / VREF) * 1023)

    read_vin = max(0, min(1023, read_vin))
    read_vout = max(0, min(1023, read_vout))

    return read_vin, read_vout, L

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            duty = int(sys.argv[1])
            vin, vout, actual_l = simulate(duty)
            print(f"{vin} {vout} {actual_l*1e6}")
        except ValueError:
            print("0 0 0")
    else:
        print("0 0 0")
