import argparse
import math
import random
import sys

def main():
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Support positional args for faster mock integration
        # Usage: python3 emulator.py <duty_8bit> <freq_hz>
        duty_8bit = float(sys.argv[1])
        freq = float(sys.argv[2])
        duty = duty_8bit / 255.0
        vin_val = 5.0
        rs_val = 0.1
        vd_val = 0.7
        l0_val = 500e-6
        rload_val = 1000.0
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--duty", type=float, default=0.5)
        parser.add_argument("--freq", type=float, default=20000)
        parser.add_argument("--vin", type=float, default=5.0)
        parser.add_argument("--rs", type=float, default=0.1)
        parser.add_argument("--vd", type=float, default=0.7)
        parser.add_argument("--l0", type=float, default=500e-6)
        parser.add_argument("--rload", type=float, default=1000.0)
        args = parser.parse_args()
        duty = args.duty
        freq = args.freq
        vin_val = args.vin
        rs_val = args.rs
        vd_val = args.vd
        l0_val = args.l0
        rload_val = args.rload

    # Model parameters
    D = duty
    T = 1.0 / freq

    # We need to solve for Vout and Ipk/L simultaneously because L depends on Ipk
    # Ipk = (Vin * D * T) / L
    # But L = f(Ipk)

    def get_l(ipk):
        # Sigmoid saturation: L(ipk) = L0 * (1 - scale / (1 + exp(-(ipk - center)/width)))
        # Make it start later: center = 0.6A, width = 0.15A
        center = 0.6
        width = 0.15
        scale = 0.8
        l_curr = l0_val * (1.0 - scale / (1.0 + math.exp(-(ipk - center)/width)))
        return l_curr

    # Fixed point iteration for Ipk and L
    ipk = (vin_val * D * T) / l0_val
    for _ in range(10):
        l_curr = get_l(ipk)
        ipk = (vin_val * D * T) / l_curr

    # Power balance: Pin_gross = Pout + Ploss_rs
    # Pin_gross = (Vin^2 * D^2 * T) / (2 * L) * (Vout + Vd) / (Vout + Vd - Vin)
    # Pout = Vout^2 / Rload
    # Iin = Pin_gross / Vin
    # Ploss_rs = Iin^2 * Rs

    p_coil = (vin_val**2 * D**2 * T) / (2 * l_curr)

    # Solve for Vout:
    # Vout^2 / Rload + (Pin_gross/Vin)^2 * Rs - Pin_gross = 0
    # where Pin_gross = p_coil * (Vout + Vd) / (Vout + Vd - Vin)

    def find_vout():
        v_low = vin_val + 0.001
        v_high = 100.0
        for _ in range(50):
            vo = (v_low + v_high) / 2
            boost = (vo + vd_val) / (vo + vd_val - vin_val)
            pg = p_coil * boost
            iin = pg / vin_val
            loss = iin**2 * rs_val
            pout = vo**2 / rload_val
            if pout + loss > pg:
                v_high = vo
            else:
                v_low = vo
        return (v_low + v_high) / 2

    vout = find_vout()
    iin = (p_coil * (vout + vd_val) / (vout + vd_val - vin_val)) / vin_val

    # Add ADC noise (~0.5% Gaussian)
    vout_noise = vout * (1.0 + random.gauss(0, 0.005))
    iin_noise = iin * (1.0 + random.gauss(0, 0.005))

    # Output for the C++ mock to read: <vin_adc> <vout_adc> <actual_l_uh>
    vin_adc = int(iin_noise * 1.0 / 5.0 * 1023)
    vout_adc = int(vout_noise / (5.0 * 10.0) * 1023)
    print(f"{vin_adc} {vout_adc} {l_curr*1e6:.3f}")

if __name__ == "__main__":
    main()
