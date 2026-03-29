import sys
import random
import math

def simulate(duty, noise=0.0):
    V_in = 5.0
    f = 100000.0
    T = 1.0 / f
    R_load = 2000.0
    L_nominal = 1.0e-3
    I_sat = 0.5     # peak current saturation threshold
    VREF = 5.0
    RIN = 1.0

    D = duty / 255.0
    if D < 0.01: return 0, int((V_in/2.0/VREF)*1023)

    t_on = D * T

    # Inductance model: sharp saturation
    I_pk_ideal = V_in * t_on / L_nominal
    if I_pk_ideal > I_sat:
        L = L_nominal / 5.0 # saturation reduces L by 5x
    else:
        L = L_nominal

    I_pk = (V_in * t_on) / L

    # Power delivered in DCM: P = 0.5 * L * I_pk^2 * f
    P_in = 0.5 * L * (I_pk**2) * f

    # SCALE for visibility on ADC
    scale = 200.0
    P_in_scaled = P_in * scale
    I_in_avg = P_in_scaled / V_in

    vin_measured = I_in_avg * RIN
    eff = 0.9
    V_out = math.sqrt(P_in_scaled * eff * R_load)
    if V_out < V_in: V_out = V_in
    vout_measured = V_out / 2.0

    read_vin = int((vin_measured / VREF) * 1023)
    read_vout = int((vout_measured / VREF) * 1023)

    read_vin = max(0, min(1023, read_vin))
    read_vout = max(0, min(1023, read_vout))

    return read_vin, read_vout

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            duty = int(sys.argv[1])
            vin, vout = simulate(duty)
            print(f"{vin} {vout}")
        except ValueError:
            print("0 0")
    else:
        print("0 0")
