import sys
import random

def simulate(duty, noise=0.01):
    VREF = 5.0
    RIN = 10
    V_supply = 5.0
    RLOAD = 2000

    D = duty / 255.0
    D_sat = 0.5

    if D < D_sat:
        # Normal operation
        eff = 0.9 + (random.random() - 0.5) * noise
        V_out = V_supply * (1.0 + D * 2.0)
        vin_measured = 0.05 + (random.random() - 0.5) * noise
    else:
        # Saturation
        extra = (D - D_sat)
        eff = 0.85 - extra * 5.0
        if eff < 0.1: eff = 0.1
        V_out = V_supply * (1.0 + D_sat * 2.0) * (1.0 - extra)
        vin_measured = 0.05 + extra * 10.0 + (random.random() - 0.5) * noise
        if vin_measured > 4.5: vin_measured = 4.5

    if V_out < 0: V_out = 0

    # analogRead values (0-1023)
    read_vin = int((vin_measured / VREF) * 1023)
    read_vout = int((V_out / 2.0 / VREF) * 1023)

    # Clamp
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
