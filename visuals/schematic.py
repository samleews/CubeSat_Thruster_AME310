import streamlit.components.v1 as components


def render_interactive_schematic(
    propellant_name: str,
    fill_pct: float,
    P_tank_MPa: float,
    T_tank_K: float,
    use_regulator: bool,
    P_reg_MPa: float,
    P_chamber_MPa: float,
    use_heater: bool,
    Q_heater_W: float,
    T_nozzle_in_K: float,
    thrust_N: float,
    isp_s: float,
    mdot_g_s: float,
    Q_wall_W: float,
    height: int = 270,
):
    """Render an interactive SVG propulsion schematic with thermodynamic hover tooltips."""
    freeze_color = "#ef4444" if T_tank_K < 230.0 else "#38bdf8"
    tank_border = "#ef4444" if T_tank_K < 230.0 else "#0ea5e9"
    reg_opacity = "1.0" if use_regulator else "0.35"
    reg_status = f"ACTIVE ({P_reg_MPa:.1f} MPa)" if use_regulator else "BYPASSED"
    htr_opacity = "1.0" if use_heater else "0.35"
    htr_status = f"Q = {Q_heater_W:.0f} W" if use_heater else "OFF"
    plume_opacity = "0.85" if thrust_N > 0.05 else "0.0"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
      body {{
        margin: 0;
        padding: 0;
        background: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #f8fafc;
        overflow: visible;
      }}
      .schematic-wrap {{
        position: relative;
        width: 100%;
        height: {height}px;
        background: #0f172a;
        border-radius: 10px;
        border: 1px solid #1e293b;
        display: flex;
        align-items: center;
        justify-content: center;
      }}
      svg {{
        width: 100%;
        height: 100%;
        max-width: 920px;
      }}
      .part {{
        cursor: pointer;
        transition: filter 0.15s ease;
      }}
      .part:hover {{
        filter: brightness(1.22);
      }}
      #tooltip {{
        position: absolute;
        display: none;
        pointer-events: none;
        background: rgba(15, 23, 42, 0.96);
        border: 1px solid #38bdf8;
        border-radius: 8px;
        padding: 10px 13px;
        font-size: 12.5px;
        line-height: 1.45;
        color: #e2e8f0;
        max-width: 280px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.55);
        z-index: 99;
      }}
      #tooltip .tt-title {{
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 4px;
        font-size: 13px;
      }}
      #tooltip .tt-eq {{
        font-family: "Cambria Math", "Times New Roman", serif;
        background: #1e293b;
        padding: 4px 7px;
        border-radius: 4px;
        margin: 5px 0;
        color: #fde68a;
        font-size: 12px;
      }}
      .hint {{
        position: absolute;
        bottom: 6px;
        right: 12px;
        font-size: 11px;
        color: #64748b;
      }}
    </style>
    </head>
    <body>
    <div class="schematic-wrap" id="wrap">
      <svg viewBox="0 0 900 240" xmlns="http://www.w3.org/2000/svg">
        <!-- Control Volume Dashed Boxes -->
        <rect x="18" y="16" width="305" height="206" rx="10" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="7,5"/>
        <text x="170" y="38" fill="#38bdf8" font-size="13" font-weight="700" text-anchor="middle">TRANSIENT TANK (VARIABLE MASS)</text>

        <rect x="348" y="16" width="534" height="206" rx="10" fill="none" stroke="#fb923c" stroke-width="2" stroke-dasharray="7,5"/>
        <text x="615" y="38" fill="#fb923c" font-size="13" font-weight="700" text-anchor="middle">SSSF THRUSTER ASSEMBLY (QUASI-STEADY)</text>

        <!-- Feed Pipes -->
        <line x1="285" y1="125" x2="390" y2="125" stroke="#94a3b8" stroke-width="7"/>
        <line x1="510" y1="125" x2="555" y2="125" stroke="#94a3b8" stroke-width="7"/>
        <line x1="675" y1="125" x2="720" y2="125" stroke="#94a3b8" stroke-width="7"/>

        <!-- 1. TANK -->
        <g class="part" data-part="tank">
          <rect x="55" y="65" width="230" height="120" rx="45" fill="#1e293b" stroke="{tank_border}" stroke-width="4"/>
          <rect x="63" y="73" width="214" height="104" rx="38" fill="{freeze_color}" fill-opacity="{max(0.12, min(0.55, fill_pct/180.0)):.2f}"/>
          <text x="170" y="114" fill="#ffffff" font-size="16" font-weight="700" text-anchor="middle">{propellant_name} ({fill_pct:.0f}%)</text>
          <text x="170" y="138" fill="#cbd5e1" font-size="13.5" text-anchor="middle">{P_tank_MPa:.2f} MPa  |  {T_tank_K:.1f} K</text>
          <text x="170" y="160" fill="#94a3b8" font-size="11.5" text-anchor="middle">Q_wall = {Q_wall_W:.1f} W</text>
        </g>

        <!-- 2. REGULATOR -->
        <g class="part" data-part="regulator" opacity="{reg_opacity}">
          <rect x="390" y="88" width="120" height="74" rx="10" fill="#1e293b" stroke="#38bdf8" stroke-width="3"/>
          <text x="450" y="120" fill="#ffffff" font-size="13.5" font-weight="700" text-anchor="middle">REGULATOR</text>
          <text x="450" y="142" fill="#38bdf8" font-size="11.5" text-anchor="middle">{reg_status}</text>
        </g>

        <!-- 3. RESISTOJET HEATER -->
        <g class="part" data-part="heater" opacity="{htr_opacity}">
          <rect x="555" y="88" width="120" height="74" rx="10" fill="#1e293b" stroke="#fb923c" stroke-width="3"/>
          <text x="615" y="120" fill="#ffffff" font-size="13.5" font-weight="700" text-anchor="middle">HEATER</text>
          <text x="615" y="142" fill="#fb923c" font-size="12" text-anchor="middle">{htr_status}</text>
        </g>

        <!-- 4. C-D NOZZLE + PLUME -->
        <g class="part" data-part="nozzle">
          <!-- Plume -->
          <polygon points="820,82 885,62 885,188 820,168" fill="#38bdf8" fill-opacity="{plume_opacity}"/>
          <!-- Nozzle body -->
          <polygon points="720,92 752,112 820,82 820,168 752,138 720,158" fill="#334155" stroke="#e2e8f0" stroke-width="3"/>
          <text x="775" y="196" fill="#f8fafc" font-size="13" font-weight="700" text-anchor="middle">F = {thrust_N:.2f} N | Isp = {isp_s:.1f} s</text>
        </g>
      </svg>

      <div id="tooltip"></div>
      <div class="hint">Hover over any component for governing equations & live state</div>
    </div>

    <script>
      const info = {{
        tank: {{
          title: "Transient Control Volume: Propellant Tank",
          eq: "dT/dt = Q_wall/(m·c_v) − (γ−1)(T/m)·ṁ",
          body: "Mass leaves during burns (dm/dt = −ṁ), causing adiabatic expansion cooling. Wall heating ({Q_wall_W:.1f} W) warms the gas during coast.<br><b>State:</b> P = {P_tank_MPa:.2f} MPa, T = {T_tank_K:.1f} K"
        }},
        regulator: {{
          title: "SSSF Device: Isenthalpic Pressure Regulator",
          eq: "h₁ = h₂ (T₂ = T₁)  |  Ṡ_gen = −ṁ·R·ln(P_c / P_tank) ≥ 0",
          body: "Throttles tank pressure down to a constant chamber pressure P_c = {P_chamber_MPa:.2f} MPa until tank pressure drops below setpoint.<br><b>Status:</b> {reg_status}"
        }},
        heater: {{
          title: "SSSF Device: Electrical Resistojet Heater",
          eq: "T_0,exit = T_in + Q_heater / (ṁ·c_p)",
          body: "Adds electrical heat ({Q_heater_W:.0f} W) to raise stagnation temperature before expansion, increasing exhaust velocity (v_e ∝ √T_0).<br><b>Nozzle Inlet T₀:</b> {T_nozzle_in_K:.1f} K"
        }},
        nozzle: {{
          title: "SSSF Device: Choked Vacuum C-D Nozzle",
          eq: "F = ṁ·v_e + P_e·A_e  |  I_sp = F / (ṁ·g₀)",
          body: "Choked at throat (M* = 1) expanding into vacuum (P_a = 0).<br><b>Live Output:</b> ṁ = {mdot_g_s:.2f} g/s, F = {thrust_N:.2f} N, I_sp = {isp_s:.1f} s"
        }}
      }};

      const tooltip = document.getElementById("tooltip");
      const wrap = document.getElementById("wrap");

      document.querySelectorAll(".part").forEach(el => {{
        el.addEventListener("mousemove", e => {{
          const key = el.getAttribute("data-part");
          const d = info[key];
          tooltip.innerHTML = `<div class="tt-title">${{d.title}}</div><div class="tt-eq">${{d.eq}}</div><div>${{d.body}}</div>`;
          tooltip.style.display = "block";
          const rect = wrap.getBoundingClientRect();
          let x = e.clientX - rect.left + 14;
          let y = e.clientY - rect.top + 14;
          if (x + 290 > rect.width) x = e.clientX - rect.left - 295;
          if (y + 130 > rect.height) y = e.clientY - rect.top - 135;
          tooltip.style.left = Math.max(8, x) + "px";
          tooltip.style.top = Math.max(8, y) + "px";
        }});
        el.addEventListener("mouseleave", () => {{
          tooltip.style.display = "none";
        }});
      }});
    </script>
    </body>
    </html>
    """
    components.html(html, height=height + 10)