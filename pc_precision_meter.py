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
import queue

class PrecisionMeterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Precision Coil Saturation Meter")
        self.root.geometry("1100x850")

        self.serial_port = None
        self.running = False
        self.data_log = []
        self.status_text = tk.StringVar(value="Disconnected")
        self.calib_results = tk.StringVar(value="Not Calibrated")
        self.port_list = []
        self.data_queue = queue.Queue()

        self.setup_ui()
        self.refresh_ports()

        # Periodic UI update from queue
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        style = ttk.Style()
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))

        # Top Control Panel
        control_frame = ttk.LabelFrame(self.root, text="Instrument Controls")
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        ttk.Label(control_frame, text="Serial Port:").pack(side=tk.LEFT, padx=5)
        self.port_combo = ttk.Combobox(control_frame, width=20)
        self.port_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="⟳", width=3, command=self.refresh_ports).pack(side=tk.LEFT)

        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=10)

        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        self.cal_btn = ttk.Button(control_frame, text="Calibrate (C)", command=self.send_calibrate, state=tk.DISABLED)
        self.cal_btn.pack(side=tk.LEFT, padx=5)

        self.sweep_btn = ttk.Button(control_frame, text="Start Sweep (S)", command=self.send_sweep, state=tk.DISABLED)
        self.sweep_btn.pack(side=tk.LEFT, padx=5)

        self.halt_btn = ttk.Button(control_frame, text="HALT (H)", command=self.send_halt, state=tk.DISABLED)
        self.halt_btn.pack(side=tk.LEFT, padx=5)

        # Status & Results Panel
        info_frame = ttk.Frame(self.root)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=15)

        ttk.Label(info_frame, text="System Status:").pack(side=tk.LEFT)
        self.status_lbl = ttk.Label(info_frame, textvariable=self.status_text, font=("Helvetica", 10, "bold"))
        self.status_lbl.pack(side=tk.LEFT, padx=5)

        ttk.Label(info_frame, text="|  Results:", style="Header.TLabel").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(info_frame, textvariable=self.calib_results, foreground="#2E7D32", font=("Courier", 11, "bold")).pack(side=tk.LEFT)

        # Plotting Area
        plt.style.use('bmh') # Better looking plots
        self.fig, self.axs = plt.subplots(2, 2, figsize=(10, 7))
        self.fig.patch.set_facecolor('#F0F0F0')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Bottom Export Panel
        export_frame = ttk.Frame(self.root)
        export_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        ttk.Button(export_frame, text="Clear Data", command=self.clear_data).pack(side=tk.LEFT, padx=5)

        ttk.Button(export_frame, text="Export CSV", command=self.save_csv).pack(side=tk.RIGHT, padx=5)
        ttk.Button(export_frame, text="Export PNG", command=self.save_plot).pack(side=tk.RIGHT, padx=5)

    def refresh_ports(self):
        self.port_list = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = self.port_list
        if self.port_list:
            self.port_combo.current(0)

    def toggle_connection(self):
        if self.serial_port is None:
            port = self.port_combo.get()
            if not port:
                messagebox.showwarning("Warning", "Select a valid COM port first.")
                return
            try:
                self.serial_port = serial.Serial(port, 115200, timeout=0.1)
                self.connect_btn.config(text="Disconnect")
                self.status_text.set("IDLE / READY")
                self.status_lbl.config(foreground="#1976D2")
                self.set_controls_state(tk.NORMAL)

                self.running = True
                self.read_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
                self.read_thread.start()
            except Exception as e:
                messagebox.showerror("Serial Error", f"Failed to connect: {e}")
        else:
            self.stop_session()

    def stop_session(self):
        self.running = False
        if self.serial_port:
            try:
                self.serial_port.write(b'H') # Send halt on disconnect
                self.serial_port.close()
            except: pass
            self.serial_port = None
        self.connect_btn.config(text="Connect")
        self.status_text.set("Disconnected")
        self.status_lbl.config(foreground="gray")
        self.set_controls_state(tk.DISABLED)

    def set_controls_state(self, state):
        self.cal_btn.config(state=state)
        self.sweep_btn.config(state=state)
        self.halt_btn.config(state=state)

    def read_serial_loop(self):
        # Buffer for incomplete lines
        buffer = ""
        while self.running:
            if self.serial_port and self.serial_port.in_waiting:
                try:
                    chunk = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        self.data_queue.put(line.strip())
                except Exception as e:
                    print(f"Read error: {e}")
            time.sleep(0.02)

    def process_queue(self):
        updated = False
        while not self.data_queue.empty():
            line = self.data_queue.get()
            if line.startswith("DATA:"):
                try:
                    vals = [float(x) for x in line.split(':')[1].split(',')]
                    if len(vals) == 5:
                        self.data_log.append(vals)
                        updated = True
                except: pass
            elif line.startswith("STATUS:"):
                status = line.split(':')[1]
                self.status_text.set(status)
                if status == "SWEEPING": self.status_lbl.config(foreground="#D32F2F")
                elif status == "CALIBRATING": self.status_lbl.config(foreground="#F57C00")
                else: self.status_lbl.config(foreground="#1976D2")
            elif line.startswith("RESULT:"):
                res = line.split(':')[1]
                self.calib_results.set(f"{res}")
            elif "HALTED" in line:
                self.status_text.set("HALTED")

        if updated:
            self.update_plots()

        self.root.after(50, self.process_queue)

    def send_calibrate(self):
        if self.serial_port:
            self.clear_data()
            self.serial_port.write(b'C')

    def send_sweep(self):
        if self.serial_port:
            self.clear_data()
            self.serial_port.write(b'S')

    def send_halt(self):
        if self.serial_port:
            self.serial_port.write(b'H')

    def clear_data(self):
        self.data_log = []
        for ax in self.axs.flat: ax.clear()
        self.canvas.draw()

    def update_plots(self):
        if not self.data_log: return

        # DUTY_PCT, VOUT, IIN, IPK, LEFF_UH
        data = list(zip(*self.data_log))
        duty = data[0]
        vout = data[1]
        iin = data[2]
        ipk = data[3]
        leff = data[4]

        # 1. Output Voltage
        self.axs[0,0].clear()
        self.axs[0,0].plot(duty, vout, color='#1976D2', marker='.', linestyle='-', markersize=4)
        self.axs[0,0].set_ylabel("Vout (V)")
        self.axs[0,0].set_title("Boost Response", fontsize=10)
        self.axs[0,0].grid(True, alpha=0.3)

        # 2. Peak Current
        self.axs[0,1].clear()
        self.axs[0,1].plot(duty, ipk, color='#D32F2F', marker='.', linestyle='-', markersize=4)
        self.axs[0,1].set_ylabel("Ipk (A)")
        self.axs[0,1].set_title("Coil Peak Current", fontsize=10)
        self.axs[0,1].grid(True, alpha=0.3)

        # 3. Inductance
        self.axs[1,0].clear()
        self.axs[1,0].plot(duty, leff, color='#388E3C', marker='.', linestyle='-', markersize=4)
        self.axs[1,0].set_ylabel("Leff (uH)")
        self.axs[1,0].set_xlabel("Duty Cycle %")
        self.axs[1,0].set_title("Inductance vs Duty", fontsize=10)
        self.axs[1,0].grid(True, alpha=0.3)

        # 4. Saturation Curve
        self.axs[1,1].clear()
        self.axs[1,1].plot(ipk, leff, color='#7B1FA2', marker='.', linestyle='-', markersize=4)
        self.axs[1,1].set_ylabel("Leff (uH)")
        self.axs[1,1].set_xlabel("Ipk (A)")
        self.axs[1,1].set_title("Saturation Profile (L vs Ipk)", fontsize=10)
        self.axs[1,1].grid(True, alpha=0.3)

        self.fig.tight_layout()
        self.canvas.draw()

    def save_csv(self):
        if not self.data_log:
            messagebox.showinfo("Info", "No data to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Duty_Pct", "Vout_V", "Iin_Avg_A", "Ipk_Calc_A", "Leff_uH"])
                    writer.writerows(self.data_log)
                messagebox.showinfo("Export Success", f"Logged {len(self.data_log)} points to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not save file: {e}")

    def save_plot(self):
        if not self.data_log:
            messagebox.showinfo("Info", "No plot data available.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if path:
            try:
                self.fig.savefig(path, dpi=150)
                messagebox.showinfo("Export Success", f"Dashboard saved to {path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not save image: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PrecisionMeterApp(root)
    # Set app icon if available, or just colors
    root.configure(bg='#F0F0F0')
    root.mainloop()
