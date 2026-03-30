import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import csv
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

class PrecisionMeterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Precision Coil Saturation Meter")
        self.root.geometry("1000x800")

        self.serial_port = None
        self.running = False
        self.data_log = []
        self.status_text = tk.StringVar(value="Disconnected")
        self.calib_results = tk.StringVar(value="Not Calibrated")

        self.setup_ui()

    def setup_ui(self):
        # Top Control Panel
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(control_frame, values=[p.device for p in serial.tools.list_ports.comports()])
        self.port_combo.pack(side=tk.LEFT, padx=5)

        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.cal_btn = ttk.Button(control_frame, text="Calibrate", command=self.send_calibrate, state=tk.DISABLED)
        self.cal_btn.pack(side=tk.LEFT, padx=5)

        self.sweep_btn = ttk.Button(control_frame, text="Start Sweep", command=self.send_sweep, state=tk.DISABLED)
        self.sweep_btn.pack(side=tk.LEFT, padx=5)

        self.halt_btn = ttk.Button(control_frame, text="HALT", command=self.send_halt, state=tk.DISABLED)
        self.halt_btn.pack(side=tk.LEFT, padx=5)

        # Status Panel
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.TOP, fill=tk.X, padx=10)
        ttk.Label(status_frame, text="Status: ").pack(side=tk.LEFT)
        ttk.Label(status_frame, textvariable=self.status_text, foreground="blue").pack(side=tk.LEFT, padx=10)
        ttk.Label(status_frame, textvariable=self.calib_results, foreground="green").pack(side=tk.RIGHT, padx=10)

        # Plotting Area
        self.fig, self.axs = plt.subplots(2, 2, figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Bottom Export Panel
        export_frame = ttk.Frame(self.root)
        export_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        ttk.Button(export_frame, text="Save CSV", command=self.save_csv).pack(side=tk.RIGHT, padx=5)
        ttk.Button(export_frame, text="Save Plot Image", command=self.save_plot).pack(side=tk.RIGHT, padx=5)
        ttk.Button(export_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)

    def toggle_connection(self):
        if self.serial_port is None:
            port = self.port_combo.get()
            if not port:
                messagebox.showerror("Error", "Please select a COM port")
                return
            try:
                self.serial_port = serial.Serial(port, 115200, timeout=0.1)
                self.connect_btn.config(text="Disconnect")
                self.status_text.set("Connected")
                self.cal_btn.config(state=tk.NORMAL)
                self.sweep_btn.config(state=tk.NORMAL)
                self.halt_btn.config(state=tk.NORMAL)

                self.running = True
                self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.read_thread.start()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            self.running = False
            self.serial_port.close()
            self.serial_port = None
            self.connect_btn.config(text="Connect")
            self.status_text.set("Disconnected")
            self.cal_btn.config(state=tk.DISABLED)
            self.sweep_btn.config(state=tk.DISABLED)
            self.halt_btn.config(state=tk.DISABLED)

    def read_serial(self):
        while self.running:
            if self.serial_port and self.serial_port.in_waiting:
                try:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line.startswith("DATA:"):
                        vals = [float(x) for x in line.split(':')[1].split(',')]
                        self.data_log.append(vals)
                        self.root.after(0, self.update_plots)
                    elif line.startswith("STATUS:"):
                        self.status_text.set(line.split(':')[1])
                    elif line.startswith("RESULT:"):
                        res = line.split(':')[1]
                        self.calib_results.set(f"Cal: {res}")
                except:
                    pass
            time.sleep(0.01)

    def send_calibrate(self):
        if self.serial_port:
            self.serial_port.write(b'C')
            self.clear_data()

    def send_sweep(self):
        if self.serial_port:
            self.clear_data()
            self.serial_port.write(b'S')

    def send_halt(self):
        if self.serial_port:
            self.serial_port.write(b'H')

    def clear_data(self):
        self.data_log = []
        self.update_plots()

    def update_plots(self):
        if not self.data_log:
            for ax in self.axs.flat: ax.clear()
            self.canvas.draw()
            return

        # DUTY_PCT, VOUT, IIN, IPK, LEFF_UH
        data = list(zip(*self.data_log))
        duty = data[0]
        vout = data[1]
        iin = data[2]
        ipk = data[3]
        leff = data[4]

        self.axs[0,0].clear()
        self.axs[0,0].plot(duty, vout, 'b.-')
        self.axs[0,0].set_title("Vout (V)")
        self.axs[0,0].grid(True)

        self.axs[0,1].clear()
        self.axs[0,1].plot(duty, ipk, 'r.-')
        self.axs[0,1].set_title("Peak Current (A)")
        self.axs[0,1].grid(True)

        self.axs[1,0].clear()
        self.axs[1,0].plot(duty, leff, 'g.-')
        self.axs[1,0].set_title("Inductance (uH)")
        self.axs[1,0].grid(True)

        self.axs[1,1].clear()
        self.axs[1,1].plot(ipk, leff, 'm.-')
        self.axs[1,1].set_title("L vs Ipk (Saturation)")
        self.axs[1,1].grid(True)

        self.fig.tight_layout()
        self.canvas.draw()

    def save_csv(self):
        if not self.data_log: return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Duty %", "Vout (V)", "Iin (A)", "Ipk (A)", "Leff (uH)"])
                writer.writerows(self.data_log)
            messagebox.showinfo("Export", f"Data saved to {path}")

    def save_plot(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if path:
            self.fig.savefig(path)
            messagebox.showinfo("Export", f"Plot saved to {path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrecisionMeterApp(root)
    root.mainloop()
