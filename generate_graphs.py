import subprocess
import matplotlib.pyplot as plt
import re

def run_test():
    result = subprocess.run(['./test_arduino'], capture_output=True, text=True)
    return result.stdout

def parse_output(output):
    duties = []
    vouts = []
    vins = []
    iins = []
    effs = []

    lines = output.split('\n')
    for line in lines:
        if line.startswith("Duty cycle:"):
            # Duty cycle: 0%	Vout: 4.99511V	Vin: 0.0478983V	Iin: 0.00478983A	Efficiency: 0.520919
            try:
                duty = float(re.search(r"Duty cycle: ([\d\.]+)%", line).group(1))
                vout = float(re.search(r"Vout: ([\d\.]+)V", line).group(1))
                vin = float(re.search(r"Vin: ([\d\.]+)V", line).group(1))
                iin = float(re.search(r"Iin: ([\d\.]+)A", line).group(1))
                eff = float(re.search(r"Efficiency: ([\d\.\-]+)", line).group(1))

                duties.append(duty)
                vouts.append(vout)
                vins.append(vin)
                iins.append(iin)
                effs.append(eff)
            except (AttributeError, ValueError):
                continue
    return duties, vouts, vins, iins, effs

def plot_results(duties, vouts, vins, iins, effs):
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    axs[0, 0].plot(duties, vouts, 'b-o')
    axs[0, 0].set_title('Output Voltage vs Duty Cycle')
    axs[0, 0].set_xlabel('Duty Cycle (%)')
    axs[0, 0].set_ylabel('Vout (V)')
    axs[0, 0].grid(True)

    axs[0, 1].plot(duties, iins, 'r-o')
    axs[0, 1].set_title('Input Current vs Duty Cycle')
    axs[0, 1].set_xlabel('Duty Cycle (%)')
    axs[0, 1].set_ylabel('Iin (A)')
    axs[0, 1].grid(True)

    axs[1, 0].plot(duties, effs, 'g-o')
    axs[1, 0].set_title('Efficiency vs Duty Cycle')
    axs[1, 0].set_xlabel('Duty Cycle (%)')
    axs[1, 0].set_ylabel('Efficiency')
    axs[1, 0].grid(True)

    axs[1, 1].plot(duties, vins, 'm-o')
    axs[1, 1].set_title('Vin (Shunt Voltage) vs Duty Cycle')
    axs[1, 1].set_xlabel('Duty Cycle (%)')
    axs[1, 1].set_ylabel('Vin (V)')
    axs[1, 1].grid(True)

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
