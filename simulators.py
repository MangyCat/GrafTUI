import numpy as np
import math
def calculate_rc_transient(v_in, cap_uf, resistances, max_time_s=0):
    """
    Calculates voltage curves for a standard DC step response (charging).
    Supports multiple resistance values (parametric sweep).
    """
    C = cap_uf * 1e-6
    results = {"curves": []}
    
    # 1. Determine Time Scale
    if max_time_s > 0:
        t_max = max_time_s
        results["mode"] = "Fixed"
    else:
        # Auto-scale to the slowest curve (max R)
        max_tau = max(resistances) * C
        t_max = 5 * max_tau
        results["mode"] = "Auto"
        
    # Generate time array (200 steps for smoothness)
    t = np.linspace(0, t_max, 200)
    results["time"] = t
    results["t_max"] = t_max
    
    # 2. Calculate Curves
    for R in resistances:
        tau = R * C
        # V(t) = V_in * (1 - e^(-t/RC))
        v_c = v_in * (1 - np.exp(-t / tau))
        
        results["curves"].append({
            "R": R,
            "tau": tau,
            "voltage": v_c
        })
        
    return results

def calculate_square_wave_response(v_in, cap_uf, res_ohm, frequency_hz, cycles=3):
    """
    Simulates an RC circuit responding to a Square Wave input (Charge/Discharge cycles).
    """
    C = cap_uf * 1e-6
    tau = res_ohm * C
    period = 1.0 / frequency_hz
    total_time = cycles * period
    
    # High resolution time steps (1000 points to capture sharp edges)
    t = np.linspace(0, total_time, 1000)
    
    v_out = np.zeros_like(t)
    v_in_wave = np.zeros_like(t)
    
    # Iterative Simulation (Time Stepping)
    dt = t[1] - t[0]
    current_v = 0.0
    
    for i, time_val in enumerate(t):
        # Generate Input Square Wave (0 or V_in)
        # First half of period is High, second half is Low
        if (time_val % period) < (period / 2):
            target_v = v_in
        else:
            target_v = 0.0
            
        v_in_wave[i] = target_v
        
        # RC Update (Euler integration): dV = (V_target - V_current) * dt / RC eulr intergration?
        change = (target_v - current_v) * (dt / tau)
        current_v += change
        v_out[i] = current_v
        #awesomeness rating: 10/10 reason: simple yet effective!
    return {
        "time": t,
        "input_wave": v_in_wave,
        "output_wave": v_out,
        "tau": tau
    }
def calculate_555_astable(r1: float, r2: float, c_uf: float, duration: float = 0.0) -> dict:
    """
    Calculates 555 Timer Astable Multivibrator behavior.
    Returns time/voltage arrays for plotting.
    """
    # Convert units
    C = c_uf * 1e-6
    
    # 555 Math
    t_high = 0.693 * (r1 + r2) * C # what is 0.693? -- ln(2)
    t_low = 0.693 * r2 * C
    period = t_high + t_low
    freq = 1.0 / period if period > 0 else 0
    duty_cycle = (t_high / period) * 100 if period > 0 else 0
    
    # Auto-duration: show 5 cycles if not specified
    if duration <= 0:
        duration = 5 * period
        
    # Generate Waveform Points
    # We construct a square wave manually
    time = []
    voltage = []
    
    t = 0
    while t < duration:
        # Rising edge
        time.append(t); voltage.append(0)
        time.append(t); voltage.append(5) # Logic High (assuming 5V)
        
        # High duration
        t += t_high
        if t > duration: break
        time.append(t); voltage.append(5)
        time.append(t); voltage.append(0) # Falling edge
        
        # Low duration
        t += t_low
        if t > duration: break
        time.append(t); voltage.append(0)

    return {
        "time": time,
        "voltage": voltage,
        "freq": freq,
        "duty": duty_cycle,
        "period": period,
        "t_high": t_high,
        "t_low": t_low
    }

def calculate_555_monostable(r_ohms: float, c_uf: float, duration: float = 0.0) -> dict:
    """
    Physically accurate 555 Monostable simulation.
    Simulates the Capacitor Voltage (Vc) charging curve.
    """
    # 1. Constants
    C = c_uf * 1e-6
    R = r_ohms
    VCC = 5.0
    V_THRESHOLD = (2/3) * VCC
    tau = R * C
    
    # Theoretical Pulse Width (for reference)
    pulse_width_theoretical = 1.1 * R * C

    # 2. Setup Timebase
    # We want to see the pulse plus some settling time
    if duration <= 0:
        duration = pulse_width_theoretical * 2.5
        if duration == 0: duration = 0.01

    points = 1000
    dt = duration / points
    
    time = []
    trigger_signal = []
    output_signal = []
    cap_voltage = [] # <--- NEW: The Blue Line in your image
    
    # 3. Simulation State
    # We assume trigger happens at 10% of the graph
    trig_time_start = duration * 0.1
    trig_time_end = trig_time_start + (duration * 0.02) # Short pulse
    
    vc = 0.0      # Capacitor Voltage
    out = 0.0     # Output Voltage
    latched = False # Internal Flip-Flop State
    
    for i in range(points):
        t = i * dt
        time.append(t)
        
        # A. Handle Trigger Input (Active Low)
        trig_val = 5.0
        if trig_time_start <= t <= trig_time_end:
            trig_val = 0.0
        trigger_signal.append(trig_val)
        
        # B. 555 Internal Logic
        
        # 1. SET Condition: Trigger < 1/3 VCC
        if trig_val < (VCC / 3):
            latched = True
            
        # 2. RESET Condition: Threshold > 2/3 VCC
        if vc >= V_THRESHOLD:
            latched = False
            
        # C. Circuit Physics
        if latched:
            # Output HIGH, Discharge Open -> Capacitor Charges through R
            out = 5.0
            # Vc_new = Vc_old + (Target - Vc_old) * (1 - exp(-dt/tau))
            # Euler integration for exponential charge
            vc = vc + (VCC - vc) * (dt / tau)
        else:
            # Output LOW, Discharge Closed -> Capacitor Shorts to Ground
            out = 0.0
            # Instant discharge (ideal 555) or fast decay
            vc = 0.0 

        output_signal.append(out)
        cap_voltage.append(vc)

    return {
        "time": time,
        "trigger": trigger_signal,
        "output": output_signal,
        "cap_voltage": cap_voltage, # Return this to plot it!
        "pulse_width": pulse_width_theoretical
    }
