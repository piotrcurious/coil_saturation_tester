import os
import pty
import serial
import time
import subprocess
import threading
import sys
import fcntl

def main():
    # Create a virtual serial port pair
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)

    # Set master to non-blocking
    flags = fcntl.fcntl(master, fcntl.F_GETFL)
    fcntl.fcntl(master, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    print(f"--- Virtual Coil Instrument v2 ---")
    print(f"Emulator logic: emulator.py")
    print(f"PC connection: {slave_name}")
    print(f"----------------------------------")

    def run_instrument_simulation(m_fd):
        is_running = False
        v_diode = 0.7
        r_series = 0.1
        l_nom = 500.0

        while True:
            # Poll for command from PC
            try:
                cmd_data = os.read(m_fd, 1)
                if not cmd_data: break
                cmd = cmd_data.decode('utf-8')
            except BlockingIOError:
                cmd = None
            except OSError:
                break

            if cmd == 'C':
                os.write(m_fd, b"STATUS:CALIBRATING\r\n")
                time.sleep(1.0) # Simulate hardware stabilization
                os.write(m_fd, b"RESULT:Vd=0.72V, Rs=0.10Ohm, Lnom=502uH\r\n")
                os.write(m_fd, b"STATUS:READY\r\n")

            elif cmd == 'S':
                is_running = True
                os.write(m_fd, b"STATUS:SWEEPING\r\n")

                for d_int in range(20, 240, 2):
                    # Check for HALT mid-sweep
                    try:
                        halt_check = os.read(m_fd, 1)
                        if halt_check.decode('utf-8') == 'H':
                            is_running = False
                            break
                    except (BlockingIOError, OSError):
                        pass

                    if not is_running: break

                    # Generate physics data
                    proc = subprocess.run(['python3', 'emulator.py', str(d_int), '20000'],
                                         capture_output=True, text=True)
                    if proc.returncode == 0:
                        vin_adc, vout_adc, act_l = proc.stdout.split()
                        vo = float(vout_adc) * 5.0 / 1023.0 * 10.0
                        ii = float(vin_adc) * 5.0 / 1023.0 / 1.0
                        D = d_int / 255.0
                        T = 1.0 / 20000.0
                        # Mock effective L with some intentional tracking lag
                        # This tests the PC side's robustness
                        ipk = (5.0 * D * T) / (float(act_l) * 1e-6)
                        data_line = f"DATA:{D*100.0:.1f},{vo:.2f},{ii:.4f},{ipk:.3f},{act_l}\r\n"
                        os.write(m_fd, data_line.encode('utf-8'))
                        time.sleep(0.02)

                is_running = False
                os.write(m_fd, b"STATUS:READY\r\n")

            elif cmd == 'H':
                is_running = False
                os.write(m_fd, b"HALTED\r\n")
                os.write(m_fd, b"STATUS:READY\r\n")

            time.sleep(0.05)

    # Start simulator in background
    t = threading.Thread(target=run_instrument_simulation, args=(master,), daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()
