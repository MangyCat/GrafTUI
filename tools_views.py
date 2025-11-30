import math
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Input, Label, RadioButton, RadioSet
from textual.screen import ModalScreen
#mul - multiplier
#tol - tolerance
#mantissa - important digits
#exponent - multiplier power of ten
#https://en.wikipedia.org/wiki/Electronic_color_code
#https://en.wikipedia.org/wiki/Ohm%27s_law
#Power is watts
class ResistorScreen(ModalScreen): # lil helper to calc resistor color codes (calc is slang for caluclate btw)
    
    COLORS = { # standard colors
        0: "black", 1: "brown", 2: "red", 3: "orange", 4: "yellow",
        5: "green", 6: "blue", 7: "violet", 8: "grey", 9: "white",
        -1: "gold", -2: "silver"
    }
    
    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("Resistor color code", classes="group-title")
            
            with RadioSet(id="band_mode_select"):
                yield RadioButton("4-Band", value=True, id="mode_4")
                yield RadioButton("5-Band", id="mode_5")

            yield Label("Enter resistance (e.g. 4.7k, 470, 4.7M)")
            
            with Horizontal(classes="setting-row"):
                yield Input(placeholder="4.7k", id="res_input")
                yield Button("CALC", id="btn_calc_res", classes="btn-primary", variant="primary")
            
            yield Label("Color bands:", id="lbl_bands_title")
            
            with Horizontal(id="band_display", classes="setting-row"):
                yield Label(" 1 ", id="band_1", classes="res-band")
                yield Label(" 2 ", id="band_2", classes="res-band")
                # Band 3 starts as ghost
                yield Label(" 3 ", id="band_3", classes="res-band")
                yield Label(" X ", id="band_mul", classes="res-band")
                yield Label(" Tol ", id="band_tol", classes="res-band")
            
            with Horizontal(classes="modal-btn-row"):
                yield Button("CLOSE", id="btn_close", variant="error")

    def on_mount(self):
        # styling inital bands
        for i in ["1", "2", "mul", "tol"]:
            self._style_active_band(f"#band_{i}")
        
        # band 3, invisible place holder (ghost)
        self._style_ghost_band("#band_3")
            
        self.query_one("#band_tol").styles.background = "gold"
        self.query_one("#band_tol").styles.color = "black"
        self.query_one("#res_input").focus()

    def _style_active_band(self, selector):
        lbl = self.query_one(selector)
        lbl.styles.width = "1fr"
        lbl.styles.height = 3
        lbl.styles.text_align = "center"
        lbl.styles.content_align = ("center", "middle")
        
        # EXPLICITLY RESTORE BORDER AND BG
        lbl.styles.background = "#333"
        lbl.styles.border = ("solid", "white")
        lbl.styles.margin = (1, 1)
        lbl.styles.opacity = 1.0 
        lbl.styles.display = "block" # Ensure it's visible

    def _style_ghost_band(self, selector): # ghost 3rd band, only way to display 4 and 5 in same ui
        lbl = self.query_one(selector)
        lbl.styles.width = "1fr"
        lbl.styles.height = 3
        lbl.styles.margin = (1, 1)
        
        # Hide visuals
        lbl.styles.background = "transparent"
        lbl.styles.border = None # Remove border
        lbl.update("") # Clear text
        lbl.styles.opacity = 0.0 # Fully invisible

    def on_radio_button_changed(self, event: RadioButton.Changed): #unused, keeping jic
        is_5_band = self.query_one("#mode_5").value
        band_tol = self.query_one("#band_tol")
        
        if is_5_band:
            # bring ghost band
            self._style_active_band("#band_3")
            band_tol.update("1%")
            band_tol.styles.background = "brown"
            band_tol.styles.color = "white"
        else:
            # no more ghost band
            self._style_ghost_band("#band_3")
            band_tol.update("5%")
            band_tol.styles.background = "gold"
            band_tol.styles.color = "black"
            
        self._calculate()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_close":
            self.dismiss()
        elif event.button.id == "btn_calc_res":
            self._calculate()
    
    def on_input_submitted(self, event: Input.Submitted): # enter key pressed
        self._calculate()

    def _calculate(self): # core calc logic
        val_str = self.query_one("#res_input").value.strip().lower()
        if not val_str:
            return
        
        is_5_band = self.query_one("#mode_5").value
        
        try:
            if val_str.endswith("k"):
                val = float(val_str[:-1]) * 1000
            elif val_str.endswith("m"):
                val = float(val_str[:-1]) * 1000000
            else:
                val = float(val_str)
        except ValueError:
            return

        if val <= 0:
            return
        if val == 0:
            return
        
        exponent = int(math.floor(math.log10(val))) # exponent, 
        
        if is_5_band:
            mantissa = val / (10**exponent)
            norm_val = int(round(mantissa * 100)) # three
            shift = exponent - 2
        else:
            mantissa = val / (10**exponent)
            norm_val = int(round(mantissa * 10)) # two
            shift = exponent - 1

        digits = [int(d) for d in str(norm_val)]
        
        if len(digits) > (3 if is_5_band else 2):
            digits = digits[:3] if is_5_band else digits[:2]
            
        while len(digits) < (3 if is_5_band else 2):
            digits.append(0)
            shift -= 1

        d1 = digits[0]
        d2 = digits[1]
        d3 = digits[2] if is_5_band else 0
        
        c1 = self.COLORS.get(d1, "black")
        c2 = self.COLORS.get(d2, "black")
        c3 = self.COLORS.get(d3, "black")
        c_mul = self.COLORS.get(shift, "black")
        
        self._set_band("#band_1", c1, str(d1))
        self._set_band("#band_2", c2, str(d2))
        
        if is_5_band:
            self._set_band("#band_3", c3, str(d3))
        else:
            self._style_ghost_band("#band_3")
            
        mul_text = "10^" + str(shift)
        if shift == -1:
            mul_text = "0.1"
        if shift == -2:
            mul_text = "0.01"
        
        self._set_band("#band_mul", c_mul, mul_text)

    def _set_band(self, band_id, color, text):
        is_5_band = self.query_one("#mode_5").value
        if band_id == "#band_3" and not is_5_band:
            return

        lbl = self.query_one(band_id)

        # Ensure that i re-assert border if it was ghosted
        if band_id == "#band_3" and is_5_band:
            lbl.styles.border = ("solid", "white")
            lbl.styles.opacity = 1.0

        lbl.styles.background = color
        lbl.styles.color = "white" if color in ["black", "blue", "brown", "red", "purple"] else "black"
        lbl.update(text)

# OHMS LAW CALCULATORR
class OhmsLawScreen(ModalScreen):
    """Calculates voltage, current, resistance, and power."""
    
    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("Ohm's law calculator", classes="group-title")
            yield Label("Enter exactly TWO values to calculate the rest.", classes="instruction-text")
            
            # Grid layout for inputs
            with Container(classes="control-group"):
                with Horizontal(classes="setting-row"):
                    yield Label("Voltage (U/V):", classes="setting-label")
                    yield Input(placeholder="Volts", id="input_v", type="number")
                
                with Horizontal(classes="setting-row"):
                    yield Label("Current (I/A):", classes="setting-label")
                    yield Input(placeholder="Amps", id="input_i", type="number")
                    
                with Horizontal(classes="setting-row"):
                    yield Label("Resistor (R/Ω):", classes="setting-label")
                    yield Input(placeholder="Ohms", id="input_r", type="number")
                    
                with Horizontal(classes="setting-row"):
                    yield Label("Power (P/W):", classes="setting-label")
                    yield Input(placeholder="Watts", id="input_p", type="number")

            with Horizontal(classes="modal-btn-row"):
                yield Button("CLEAR", id="btn_clear", classes="btn-secondary")
                yield Button("CALCULATE", id="btn_calc", classes="btn-primary", variant="primary")
                
            with Horizontal(classes="modal-btn-row"):
                yield Button("CLOSE", id="btn_close", variant="error")

    def on_mount(self):
        self.query_one("#input_v").focus()

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "btn_close":
            self.dismiss()
        elif btn_id == "btn_clear":
            for i in ["v", "i", "r", "p"]:
                self.query_one(f"#input_{i}").value = ""
            self.query_one("#input_v").focus()
        elif btn_id == "btn_calc":
            self._calculate()

    def _calculate(self):
        # gather inputs
        inputs = {}
        for key in ["v", "i", "r", "p"]:
            val_str = self.query_one(f"#input_{key}").value.strip()
            if val_str:
                try:
                    inputs[key] = float(val_str)
                except ValueError:
                    pass
        
        if len(inputs) < 2:
            self.notify("Please enter at least 2 values.", severity="warning")
            return

        # solve
        # 6 combos of 2 inputs

        v = inputs.get("v")
        i = inputs.get("i")
        r = inputs.get("r")
        p = inputs.get("p")
        try:
            if v is not None and i is not None: # Given v, i 
                r = v / i if i != 0 else 0
                p = v * i
            elif v is not None and r is not None: # Given V, R
                i = v / r if r != 0 else 0
                p = (v**2) / r if r != 0 else 0
            elif v is not None and p is not None: # Given V, P
                i = p / v if v != 0 else 0
                r = (v**2) / p if p != 0 else 0
            elif i is not None and r is not None: # Given I, R
                v = i * r
                p = (i**2) * r
            elif i is not None and p is not None: # Given I, P
                v = p / i if i != 0 else 0
                r = p / (i**2) if i != 0 else 0
            elif p is not None and r is not None: # Given P, R
                v = math.sqrt(p * r)
                i = math.sqrt(p / r) if r != 0 else 0

            # 3. Update UI
            self._update_field("v", v)
            self._update_field("i", i)
            self._update_field("r", r)
            self._update_field("p", p)
        except (ValueError, ZeroDivisionError, TypeError) as e:
            self.notify(f"Math Error: {e}", severity="error")

    def _update_field(self, key, val): # update field
        if val is None:
            return
        inp = self.query_one(f"#input_{key}")
        inp.value = f"{val:.4f}"
