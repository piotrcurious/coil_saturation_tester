import sys
import random
import math

# Realistic Boost Converter Physics Emulator
def simulate(duty, f=20000.0, noise=0.0005):
    V_in = 5.0
    T = 1.0 / f
    R_load = 500.0
    L0 = 500e-6
    Isat = 0.5      # Lowered to see more saturation
    V_d = 0.7       # Realistic Schottky/Silicon mix
    R_s = 0.3
    VREF = 5.0
    RIN = 1.0

    D = duty / 255.0
    if D < 0.001:
        V_out_off = max(0, V_in - V_d)
        return 0, int((V_out_off / 10.0 / VREF) * 1023), L0

    t_on = D * T

    # Physics with saturation
    phase = (V_in * t_on) / (L0 * Isat)
    if phase > 1.56: phase = 1.56
    I_pk = Isat * math.tan(phase)
    E_on = - L0 * (Isat**2) * math.log(math.cos(phase))

    # V_out(V_out + V_d - V_in) = f * E_on * R_load
    K = f * E_on * R_load
    b = V_d - V_in
    V_out = (-b + math.sqrt(b**2 + 4*K)) / 2.0
    V_out = max(V_out, V_in - V_d)

    P_out = V_out**2 / R_load

    # I_in * V_in = P_out + I_in^2 * R_s + P_diode
    # P_diode = I_out_avg * V_d.
    # In DCM, I_out_avg = I_in_avg * (Vin / Vout) approx.
    # Let's simplify: P_in_gross = P_out + Losses
    # I_in = (P_out / (V_out/(V_out+V_d))) / V_in ?
    # Let's use: Pin = Pout * (Vout + Vd) / Vout + Iin^2 * Rs
    # Pin = Pout * (1 + Vd/Vout) + Iin^2 * Rs
    P_net = P_out * (1.0 + V_d/V_out)

    # Rs * Iin^2 - Vin * Iin + P_net = 0
    disc = V_in**2 - 4 * R_s * P_net
    if disc < 0: I_in_avg = V_in / (2 * R_s)
    else: I_in_avg = (V_in - math.sqrt(disc)) / (2 * R_s)

    L_actual = L0 / (1.0 + (I_pk / Isat)**2)

    read_vin = int((I_in_avg * RIN / VREF) * 1023 + (random.random()-0.5) * noise * 1023)
    read_vout = int((V_out / 10.0 / VREF) * 1023 + (random.random()-0.5) * noise * 1023)

    return max(0, min(1023, read_vin)), max(0, min(1023, read_vout)), L_actual

if __name__ == "__main__":
    freq = 20000.0
    if len(sys.argv) > 2:
        try: freq = float(sys.argv[2])
        except: pass

    if len(sys.argv) > 1:
        try:
            duty = int(sys.argv[1])
            vin, vout, actual_l = simulate(duty, f=freq)
            print(f"{vin} {vout} {actual_l*1e6}")
        except:
            print("0 0 0")
    else:
        print("0 0 0")
