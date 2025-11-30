import statistics
import math

class StatsEngine:
    """Central logic for calculating signal statistics."""

    @staticmethod
    def calculate_generic(data_input, name: str = "Series") -> str:
        if data_input is None: return "No Data"
        try:
            data_list = list(data_input)
            clean_data = [float(x) for x in data_list if x is not None]
            if not clean_data: return "Empty Data"

            count = len(clean_data) # ship or 
            min_val = min(clean_data)
            max_val = max(clean_data)
            mean_val = statistics.mean(clean_data)
            try: stdev_val = statistics.stdev(clean_data)
            except: stdev_val = 0.0

            return (
                f"Target: {name}\n"
                f"Count: {count}\n"
                f"Min: {min_val:.4f}\n"
                f"Max: {max_val:.4f}\n"
                f"Mean: {mean_val:.4f}\n"
                f"StdDev: {stdev_val:.4f}"
            )
        except: return "Stats Error"

    @staticmethod
    def analyze_simulation(data: dict, mode: str) -> str:
        """Analyzes simulation results based on circuit type."""
        try:
            if mode == "rc_step":
                # Analyze the first curve usually
                if not data.get("curves"): return "No Curves"
                # Just pick the first one for stats
                c0 = data["curves"][0]
                tau = c0.get("tau", 0)
                R = c0.get("R", 0)
                return (
                    f"Type: RC Step\n"
                    f"Res: {R} Ω\n"
                    f"Tau: {tau:.4f} s\n"
                    f"5*Tau: {5*tau:.4f} s"
                )

            elif mode == "rc_square":
                # Fix: Handle output_wave instead of voltage
                tau = data.get("tau", 0)
                out_wave = data.get("output_wave", [])
                
                v_pk = max(out_wave) if len(out_wave) > 0 else 0
                v_min = min(out_wave) if len(out_wave) > 0 else 0
                
                return (
                    f"Type: RC Filter (AC)\n"
                    f"Tau: {tau:.4f} s\n"
                    f"V_peak: {v_pk:.2f} V\n"
                    f"V_min: {v_min:.2f} V"
                )

            elif mode == "555_astable":
                freq = data.get("freq", 0)
                duty = data.get("duty", 0)
                return (
                    f"Type: 555 Astable\n"
                    f"Freq: {freq:.2f} Hz\n"
                    f"Duty: {duty:.1f} %\n"
                    f"Period: {1/freq if freq>0 else 0:.4f} s"
                )

            elif mode == "555_mono":
                pw = data.get("pulse_width", 0)
                return (
                    f"Type: 555 Mono\n"
                    f"Pulse: {pw:.4f} s\n"
                    f"Triggered: Yes"
                )

            return "Unknown Mode"

        except Exception as e:
            return f"Sim Stats Error: {str(e)}"