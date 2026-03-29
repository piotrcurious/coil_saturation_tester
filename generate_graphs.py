import subprocess
import matplotlib.pyplot as plt
import re

def run_test():
    result = subprocess.run(['./test_arduino'], capture_output=True, text=True)
    return result.stdout

def parse_output(output):
    duties = []
    vouts = []
    iins = []
    ipks = []
    inferred_ls = []
    actual_ls = []

    last_actual_l = 1000.0

    lines = output.split('\n')
    for line in lines:
        if line.startswith("ActualL:"):
            match = re.search(r"ActualL: ([\d\.]+) uH", line)
            if match:
                last_actual_l = float(match.group(1))

        if line.startswith("Duty cycle:"):
            # Duty cycle: 10%	Vout: 8.31867V	Iin_avg: 0.00488759A	Ipk: 0.123A	InferredL: 7.86621 uH
            try:
                duty_match = re.search(r"Duty cycle: ([\d\.]+)%", line)
                vout_match = re.search(r"Vout: ([\d\.]+)V", line)
                iin_match = re.search(r"Iin_avg: ([\d\.]+)A", line)
                ipk_match = re.search(r"Ipk: ([\d\.]+)A", line)
                l_match = re.search(r"InferredL: ([\d\.]+) uH", line)

                if duty_match and vout_match and iin_match and l_match:
                    duty = float(duty_match.group(1))
                    vout = float(vout_match.group(1))
                    iin = float(iin_match.group(1))
                    ipk = float(ipk_match.group(1)) if ipk_match else 0.0
                    l_val = float(l_match.group(1))

                    duties.append(duty)
                    vouts.append(vout)
                    iins.append(iin)
                    ipks.append(ipk)
                    inferred_ls.append(l_val)
                    actual_ls.append(last_actual_l)
            except (ValueError):
                continue
    return duties, vouts, iins, ipks, inferred_ls, actual_ls

def plot_results(duties, vouts, iins, ipks, inferred_ls, actual_ls):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    axs[0, 0].plot(duties, vouts, 'b-o', label='Vout')
    axs[0, 0].set_title('Output Voltage vs Duty Cycle')
    axs[0, 0].set_xlabel('Duty Cycle (%)')
    axs[0, 0].set_ylabel('Vout (V)')
    axs[0, 0].grid(True)
    axs[0, 0].legend()

    axs[0, 1].plot(duties, ipks, 'r-o', label='Peak Current (Ipk)')
    axs[0, 1].set_title('Peak Current vs Duty Cycle')
    axs[0, 1].set_xlabel('Duty Cycle (%)')
    axs[0, 1].set_ylabel('Ipk (A)')
    axs[0, 1].grid(True)
    axs[0, 1].legend()

    corrected_inferred_ls = [l * 200.0 for l in inferred_ls]

    axs[1, 0].plot(duties, corrected_inferred_ls, 'g-o', label='Inferred L')
    axs[1, 0].plot(duties, actual_ls, 'k--', label='Actual L')
    axs[1, 0].set_title('Inductance vs Duty Cycle')
    axs[1, 0].set_xlabel('Duty Cycle (%)')
    axs[1, 0].set_ylabel('L (uH)')
    axs[1, 0].grid(True)
    axs[1, 0].legend()

    # Inferred L vs Peak Current
    axs[1, 1].plot(ipks, corrected_inferred_ls, 'm-o', label='L vs Ipk')
    axs[1, 1].set_title('Inductance vs Peak Current')
    axs[1, 1].set_xlabel('Peak Current (A)')
    axs[1, 1].set_ylabel('L (uH)')
    axs[1, 1].grid(True)
    axs[1, 1].legend()

    plt.tight_layout()
    plt.savefig('test_results.png')
    print("Graph saved as test_results.png")

if __name__ == "__main__":
    print("Running simulation...")
    output = run_test()
    print("Parsing results...")
    data = parse_output(output)
    if data[0]:
        print(f"Generating graphs for {len(data[0])} data points...")
        plot_results(*data)
    else:
        print("No data points found to plot.")
