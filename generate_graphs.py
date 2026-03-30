import sys
import os
import subprocess
import matplotlib.pyplot as plt
import re

def run_simulation():
    # Run the compiled arduino mock
    # It should produce output to stdout
    process = subprocess.Popen(['./arduino_app'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout

def parse_output(output):
    duty_cycles = []
    vouts = []
    vins = []
    iins = []
    ipks = []
    l_inferred = []
    l_actual = []

    # Calibration results
    best_vd = 0
    best_rs = 0

    lines = output.split('\n')
    last_actual_l = 500.0
    for line in lines:
        if "CALIBRATED_VD:" in line:
            best_vd = float(line.split(':')[1])
            continue
        if "CALIBRATED_RS:" in line:
            best_rs = float(line.split(':')[1])
            continue

        if "ActualL:" in line:
            try:
                last_actual_l = float(line.split(':')[1].split()[0])
            except:
                pass
            continue

        # D:7.8% Vo:5.03V Ii:0.0098A Ip:0.039A Le:500.00uH
        if line.startswith("D:"):
            try:
                # Use regex for more robust parsing
                d_m = re.search(r"D:([\d.]+)", line)
                vo_m = re.search(r"Vo:([\d.]+)", line)
                ii_m = re.search(r"Ii:([\d.]+)", line)
                ip_m = re.search(r"Ip:([\d.]+)", line)
                le_m = re.search(r"Le:([\d.]+)", line)

                if d_m and vo_m and ii_m and ip_m and le_m:
                    duty_cycles.append(float(d_m.group(1)))
                    vouts.append(float(vo_m.group(1)))
                    iins.append(float(ii_m.group(1)))
                    ipks.append(float(ip_m.group(1)))
                    l_inferred.append(float(le_m.group(1)))
                    l_actual.append(last_actual_l)
            except Exception as e:
                print(f"Error parsing line: {line} -> {e}")
                continue

    return {
        'duty': duty_cycles,
        'vin': vins,
        'vout': vouts,
        'iin': iins,
        'ipk': ipks,
        'l_inf': l_inferred,
        'l_act': l_actual,
        'best_vd': best_vd,
        'best_rs': best_rs
    }

def plot_results(data):
    fig, axs = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Vout vs Duty
    axs[0, 0].plot(data['duty'], data['vout'], 'b.-', label='Actual Vout')
    # Ideal Boost CCM for reference (gray dashed)
    Vin = 5.0
    ideal_vout = []
    for d in data['duty']:
        D = d / 100.0
        if D < 0.95:
            v = Vin / (1.0 - D)
        else:
            v = Vin / 0.05
        ideal_vout.append(v)
    axs[0, 0].plot(data['duty'], ideal_vout, 'k--', alpha=0.3, label='Ideal Boost (CCM Reference)')
    axs[0, 0].set_title("Output Voltage")
    axs[0, 0].set_xlabel("Duty Cycle %")
    axs[0, 0].set_ylabel("V (V)")
    axs[0, 0].legend()
    axs[0, 0].grid(True)

    # 2. Peak Current vs Duty
    axs[0, 1].plot(data['duty'], data['ipk'], 'r.-')
    axs[0, 1].set_title("Peak Current")
    axs[0, 1].set_xlabel("Duty Cycle %")
    axs[0, 1].set_ylabel("I (A)")
    axs[0, 1].grid(True)

    # 3. Inductance vs Duty
    axs[0, 2].plot(data['duty'], data['l_inf'], 'g.-', label='Inferred Effective L')
    axs[0, 2].plot(data['duty'], data['l_act'], 'k--', label='Actual Instantaneous L')
    axs[0, 2].set_title("Inductance (Effective vs Instantaneous)")
    axs[0, 2].set_xlabel("Duty Cycle %")
    axs[0, 2].set_ylabel("L (uH)")
    axs[0, 2].legend()
    axs[0, 2].grid(True)

    # 4. Saturation Curve (L vs Ipk)
    axs[1, 0].plot(data['ipk'], data['l_inf'], 'm.-', label='Inferred Effective')
    axs[1, 0].plot(data['ipk'], data['l_act'], 'k--', alpha=0.5, label='Actual Instantaneous')
    axs[1, 0].set_title("Saturation Tracking (L vs Ipk)")
    axs[1, 0].set_xlabel("Ipk (A)")
    axs[1, 0].set_ylabel("L (uH)")
    axs[1, 0].legend()
    axs[1, 0].grid(True)

    # 5. Error %
    error = [(inf - act)/act * 100 for inf, act in zip(data['l_inf'], data['l_act'])]
    axs[1, 1].plot(data['duty'], error, 'k.-')
    axs[1, 1].axhline(0, color='r', alpha=0.5)
    axs[1, 1].set_title("Effective vs Instantaneous Difference %")
    axs[1, 1].set_xlabel("Duty Cycle %")
    axs[1, 1].set_ylabel("Difference %")
    axs[1, 1].set_ylim(-20, 150)
    axs[1, 1].grid(True)

    # 6. Input Current
    axs[1, 2].plot(data['duty'], data['iin'], 'c.-')
    axs[1, 2].set_title("Average Input Current")
    axs[1, 2].set_xlabel("Duty Cycle %")
    axs[1, 2].set_ylabel("Iin (A)")
    axs[1, 2].grid(True)

    plt.tight_layout()
    plt.savefig('test_results.png')
    print("Graphs saved to test_results.png")

    print(f"Final Calibration: Vd={data['best_vd']:.3f}V, Rs={data['best_rs']:.3f} Ohm")
    if len(error) > 0:
        avg_err = sum(abs(e) for e in error) / len(error)
        print(f"Avg Difference (Inferred vs Instantaneous): {avg_err:.2f}%")

if __name__ == "__main__":
    output = run_simulation()
    data = parse_output(output)
    if not data['duty']:
        print("No data parsed! Check simulation output.")
        print(output[:500])
    else:
        plot_results(data)
