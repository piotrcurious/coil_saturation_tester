import os
import pty
import serial
import time
import subprocess
import threading
import sys

def main():
    # Create a virtual serial port pair using PTY
    master, slave = pty.openpty()
    slave_name = os.ttyname(slave)
    print(f"Virtual Serial Port Created: {slave_name}")
    print(f"Connect your PC Tool to: {slave_name}")

    def run_firmware_logic(master_fd):
        # We simulate the precision_coil_meter.ino logic here
        # It reads commands 'C', 'S', 'H' from master_fd
        # It writes responses to master_fd

        current_l_nom = 500.0
        is_running = False

        while True:
            # Check for commands
            try:
                cmd_raw = os.read(master_fd, 1)
                if not cmd_raw: break
                cmd = cmd_raw.decode('utf-8')
            except OSError:
                break

            if cmd == 'C':
                os.write(master_fd, b"STATUS:CALIBRATING\r\n")
                time.sleep(1) # Simulate calibration
                os.write(master_fd, b"RESULT:VD=1.00\r\n")
                os.write(master_fd, b"RESULT:RS=0.10\r\n")
                os.write(master_fd, b"RESULT:LNOM=490.5\r\n")
                os.write(master_fd, b"STATUS:READY\r\n")

            elif cmd == 'S':
                os.write(master_fd, b"STATUS:SWEEPING\r\n")
                # Simulate a sweep using emulator.py
                for duty_int in range(20, 240, 2):
                    # Use emulator.py to get realistic values
                    # python3 emulator.py <duty_8bit> <freq_hz>
                    # Returns: <vin_adc> <vout_adc> <actual_l_uh>
                    proc = subprocess.run(['python3', 'emulator.py', str(duty_int), '20000'],
                                         capture_output=True, text=True)
                    if proc.returncode == 0:
                        vin_adc, vout_adc, actual_l = proc.stdout.split()

                        # Convert ADC back to Volts for the telemetry
                        # vout = adc * 5.0 / 1023.0 * 10.0
                        # iin = adc * 5.0 / 1023.0 / 1.0
                        vo = float(vout_adc) * 5.0 / 1023.0 * 10.0
                        ii = float(vin_adc) * 5.0 / 1023.0 / 1.0
                        D = duty_int / 255.0
                        T = 1.0 / 20000.0

                        # Simplified Ipk for the mock
                        ipk = (5.0 * D * T) / (float(actual_l) * 1e-6)

                        # DATA:DUTY_PCT,VOUT,IIN,IPK,LEFF_UH
                        data_line = f"DATA:{D*100.0:.1f},{vo:.2f},{ii:.4f},{ipk:.3f},{actual_l}\r\n"
                        os.write(master_fd, data_line.encode('utf-8'))
                        time.sleep(0.05)

                        # Check for halt
                        # (Non-blocking check would be better, but simplified for now)

                os.write(master_fd, b"STATUS:READY\r\n")

            elif cmd == 'H':
                is_running = False
                os.write(master_fd, b"HALTED\r\n")
                os.write(master_fd, b"STATUS:READY\r\n")

    # Start the simulation in a background thread
    sim_thread = threading.Thread(target=run_firmware_logic, args=(master,), daemon=True)
    sim_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down virtual serial bridge.")

if __name__ == "__main__":
    main()
