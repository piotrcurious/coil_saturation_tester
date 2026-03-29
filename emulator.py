import sys

def simulate(duty):
    VREF = 5.0
    RIN = 10
    V_supply = 5.0
    RLOAD = 2000

    D = duty / 255.0
    D_sat = 0.5

    if D < D_sat:
        # Normal operation
        V_out = V_supply * (1.0 + D * 2.0)
        # Current is small
        vin_measured = 0.05 # 50mV across shunt
    else:
        # Saturation
        extra = (D - D_sat)
        V_out = V_supply * (1.0 + D_sat * 2.0) * (1.0 - extra)
        # Current spikes!
        vin_measured = 0.05 + extra * 10.0 # Rapidly increases
        if vin_measured > 4.0: vin_measured = 4.0

    # analogRead values (0-1023)
    read_vin = int((vin_measured / VREF) * 1023)
    read_vout = int((V_out / 2.0 / VREF) * 1023) # Vout divider

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
