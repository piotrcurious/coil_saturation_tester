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
    ls = []

    lines = output.split('\n')
    for line in lines:
        if line.startswith("Duty cycle:"):
            # Duty cycle: 10%	Vout: 8.31867V	Iin_avg: 0.00488759A	Inferred L: 7.86621 uH
            try:
                duty = float(re.search(r"Duty cycle: ([\d\.]+)%", line).group(1))
                vout = float(re.search(r"Vout: ([\d\.]+)V", line).group(1))
                iin = float(re.search(r"Iin_avg: ([\d\.]+)A", line).group(1))
                l_val = float(re.search(r"Inferred L: ([\d\.]+) uH", line).group(1))

                duties.append(duty)
                vouts.append(vout)
                iins.append(iin)
                ls.append(l_val)
            except (AttributeError, ValueError):
                continue
    return duties, vouts, iins, ls

def plot_results(duties, vouts, iins, ls):
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    axs[0, 0].plot(duties, vouts, 'b-o')
    axs[0, 0].set_title('Output Voltage vs Duty Cycle')
    axs[0, 0].set_xlabel('Duty Cycle (%)')
    axs[0, 0].set_ylabel('Vout (V)')
    axs[0, 0].grid(True)

    axs[0, 1].plot(duties, iins, 'r-o')
    axs[0, 1].set_title('Avg Input Current vs Duty Cycle')
    axs[0, 1].set_xlabel('Duty Cycle (%)')
    axs[0, 1].set_ylabel('Iin_avg (A)')
    axs[0, 1].grid(True)

    axs[1, 0].plot(duties, ls, 'g-o')
    axs[1, 0].set_title('Inferred Inductance vs Duty Cycle')
    axs[1, 0].set_xlabel('Duty Cycle (%)')
    axs[1, 0].set_ylabel('Inferred L (uH)')
    axs[1, 0].grid(True)

    # Empty or additional plot
    axs[1, 1].axis('off')
    axs[1, 1].text(0.1, 0.5, "Saturation detection based on\nInferred Inductance drop.", fontsize=12)

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
        print("Output was:")
        print(output)
