import subprocess
import matplotlib.pyplot as plt
import re

def run_test():
    result = subprocess.run(['./test_arduino'], capture_output=True, text=True)
    return result.stdout

def parse_output(output):
    d = []
    vo = []
    ii = []
    ip = []
    le = []
    la = []

    last_la = 1000.0

    lines = output.split('\n')
    for line in lines:
        if line.startswith("ActualL:"):
            m = re.search(r"ActualL: ([\d\.]+) uH", line)
            if m: last_la = float(m.group(1))

        if line.startswith("D:"):
            try:
                m_d = re.search(r"D:([\d\.]+)%", line)
                m_v = re.search(r"Vo:([\d\.]+)V", line)
                m_i = re.search(r"Ii:([\d\.]+)A", line)
                m_p = re.search(r"Ip:([\d\.]+)A", line)
                m_l = re.search(r"Le:([\d\.]+)uH", line)

                if m_d and m_v and m_i and m_p and m_l:
                    d.append(float(m_d.group(1)))
                    vo.append(float(m_v.group(1)))
                    ii.append(float(m_i.group(1)))
                    ip.append(float(m_p.group(1)))
                    le.append(float(m_l.group(1)))
                    la.append(last_la)
            except: continue
    return d, vo, ii, ip, le, la

def plot_results(d, vo, ii, ip, le, la):
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))

    axs[0, 0].plot(d, vo, 'b-o', markersize=3, label='Actual Vout')
    theoretical_vo = [5.0 / (1.0 - (x/100.0) + 0.001) for x in d]
    axs[0, 0].plot(d, theoretical_vo, 'k--', alpha=0.5, label='Ideal Boost (CCM)')
    axs[0, 0].set_title('Output Voltage')
    axs[0, 0].set_ylabel('V (V)')
    axs[0, 0].grid(True)
    axs[0, 0].legend()

    axs[0, 1].plot(d, ip, 'r-o', markersize=3, label='Peak Current')
    axs[0, 1].set_title('Peak Current')
    axs[0, 1].set_ylabel('I (A)')
    axs[0, 1].grid(True)

    axs[1, 0].plot(d, le, 'g-o', markersize=3, label='Inferred L')
    axs[1, 0].plot(d, la, 'k--', label='Actual L')
    axs[1, 0].set_title('Inductance')
    axs[1, 0].set_ylabel('L (uH)')
    axs[1, 0].grid(True)
    axs[1, 0].legend()

    axs[1, 1].plot(ip, le, 'm-o', markersize=3)
    axs[1, 1].set_title('L vs Peak Current')
    axs[1, 1].set_xlabel('Ipk (A)')
    axs[1, 1].set_ylabel('L (uH)')
    axs[1, 1].grid(True)

    plt.tight_layout()
    plt.savefig('test_results.png')
    print("Graph saved as test_results.png")

if __name__ == "__main__":
    print("Running simulation...")
    output = run_test()
    data = parse_output(output)
    if data[0]: plot_results(*data)
    else: print("No data.")
