GUIDED_STEPS = [
    {
        "title": "Step 1 of 5 — Meet the Components",
        "summary": (
            "Your CubeSat propulsion system connects two thermodynamic control volumes:\n"
            "- **Transient Tank (Blue):** Stores pressurized gas. As gas vents, mass, pressure, and temperature drop over time.\n"
            "- **SSSF Nozzle (Orange):** Always choked in vacuum ($P_a = 0$), converting thermal energy into supersonic exhaust thrust.\n"
            "- **Optional Regulator:** Caps nozzle inlet pressure for steady thrust.\n"
            "- **Optional Resistojet Heater:** Adds electrical heat ($\\dot{Q}$) before the nozzle to boost exhaust velocity and $I_{sp}$."
        ),
        "prompt": "Click the **Baseline** quick preset in the sidebar (or keep **Regulator OFF** and **Heater OFF** in Core Controls), then hit **▶ Play** to observe a baseline adiabatic blowdown.",
        "check": lambda cfg: cfg["gas_key"] == "Nitrogen (N2)" and not cfg["use_regulator"] and not cfg["use_heater"],
        "hint": "Click 'Baseline' under Quick Presets at the top of the sidebar.",
    },
    {
        "title": "Step 2 of 5 — Trigger & Observe Valve Freezing",
        "summary": (
            "Rapid adiabatic expansion cools the remaining gas inside the tank ($T \\propto P^{(\\gamma-1)/\\gamma}$). "
            "If tank temperature drops below **230 K**, thruster valve seals can freeze and fail."
        ),
        "prompt": "Click the **Freeze Risk** quick preset (or enable **Advanced Controls** and raise Throat Diameter ≥ 1.8 mm). Switch the live graph to **Tank Temperature T(t) [K]** and hit **▶ Play** to see the red **Valve Freeze** annotation.",
        "check": lambda cfg: cfg["d_throat_mm"] >= 1.8 and cfg["min_T"] < 230.0,
        "hint": "Click 'Freeze Risk' under Quick Presets so the tank blows down fast enough to drop below 230 K.",
    },
    {
        "title": "Step 3 of 5 — Stabilize Thrust with the Pressure Regulator",
        "summary": (
            "In unregulated blowdown mode, thrust decays continuously as tank pressure falls. "
            "Enabling the **Pressure Regulator** throttles the gas isenthalpically ($h_1 = h_2$) to a constant chamber pressure until tank pressure drops to the setpoint."
        ),
        "prompt": "In **Core Controls**, turn **Enable Pressure Regulator ON**, adjust the **Regulator Setpoint** slider that appears (e.g., **5.0 MPa**), switch the graph to **Thruster Force F(t) [N]**, and hit **▶ Play**.",
        "check": lambda cfg: cfg["use_regulator"],
        "hint": "Toggle 'Enable Pressure Regulator' ON inside Core Controls.",
    },
    {
        "title": "Step 4 of 5 — Save Two Runs for Comparison (Cold-Gas vs. Resistojet)",
        "summary": (
            "Exhaust velocity scales with $\\sqrt{T_0 / M}$. To quantify how much a **Resistojet Heater** improves performance, "
            "save two runs and overlay them directly in **Comparison Mode**."
        ),
        "prompt": "1) With **Heater OFF**, click **💾 Save as Case A** above.  2) Turn **Enable Resistojet Heater ON**, set **Heater Power ≥ 50 W** right below it, and click **💾 Save as Case B**.",
        "check": lambda cfg: cfg["has_case_a"] and cfg["has_case_b"] and cfg["use_heater"] and cfg["Q_heater"] >= 50.0,
        "hint": "Save an unheated run as Case A, then toggle 'Enable Resistojet Heater' ON (≥ 50 W) in Core Controls and click Save as Case B.",
    },
    {
        "title": "Step 5 of 5 — Analyze Trade-Offs in Comparison Mode",
        "summary": (
            "**Comparison Mode** lets you inspect side-by-side deltas in $\\Delta v$, propellant usage, peak $I_{sp}$, "
            "and overlaid time-series curves."
        ),
        "prompt": "Select **Comparison Mode** in the top navigation bar to compare Case A vs. Case B! *(Bonus: toggle **⚙️ Advanced Controls** ON to switch Propellant Gas to **Helium (He)** and compare molar mass effects.)*",
        "check": lambda cfg: cfg["has_case_a"] and cfg["has_case_b"],
        "hint": "Make sure both Case A and Case B are saved, then click Comparison Mode in the top bar.",
    },
]