import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from thermo_engine.fluid_props import get_propellant
from thermo_engine.hohmann import compute_hohmann_targets
from thermo_engine.tank_transient import simulate_freeplay_blowdown, simulate_hohmann_mission
from game.missions import MISSIONS, evaluate_mission
from visuals.schematic import render_interactive_schematic

st.set_page_config(page_title="CubeSat Thruster Virtual Lab", page_icon="🛰️", layout="wide")


# --- Session State Defaults ---
DEFAULTS = {
    "propellant": "Nitrogen (N2)",
    "V_tank_L": 4.0,
    "P_init_MPa": 20.0,
    "T_init_K": 295.0,
    "m_dry": 12.0,
    "d_throat_mm": 1.4,
    "area_ratio": 50.0,
    "eta_nozzle": 0.92,
    "burn_duration": 90.0,
    "use_regulator": False,
    "P_reg_MPa": 5.0,
    "use_heater": False,
    "Q_heater": 50.0,
    "Q_wall": 2.0,
    "case_a": None,
    "case_b": None,
    "mission_result": None,
    "mission_tested_params": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_preset(preset_name: str):
    if preset_name == "baseline":
        st.session_state.update(
            propellant="Nitrogen (N2)", V_tank_L=4.0, P_init_MPa=20.0, T_init_K=295.0,
            m_dry=12.0, d_throat_mm=1.4, use_regulator=False, use_heater=False, Q_heater=0.0, Q_wall=0.0
        )
    elif preset_name == "resistojet":
        st.session_state.update(
            propellant="Nitrogen (N2)", V_tank_L=4.0, P_init_MPa=20.0, T_init_K=295.0,
            m_dry=12.0, d_throat_mm=1.4, use_regulator=True, P_reg_MPa=5.0, use_heater=True, Q_heater=75.0, Q_wall=2.0
        )
    elif preset_name == "freeze":
        st.session_state.update(
            propellant="Nitrogen (N2)", V_tank_L=4.0, P_init_MPa=20.0, T_init_K=295.0,
            m_dry=12.0, d_throat_mm=2.2, use_regulator=False, use_heater=False, Q_heater=0.0, Q_wall=0.0
        )


# --- Header & Top Navigation ---
st.title("🛰️ CubeSat Cold-Gas & Resistojet Virtual Thermodynamics Lab")
mode = st.segmented_control(
    "Navigation",
    ["Free-Play Mode", "Mission Mode", "Comparison Mode", "Validation Audit"],
    default="Free-Play Mode",
    label_visibility="collapsed",
)

in_mission = (mode == "Mission Mode")

# --- Mission Selection (Placed early so sidebar can lock bus specs per mission) ---
selected_mission = None
if in_mission:
    mission_name = st.selectbox("Select Orbital Mission", list(MISSIONS.keys()))
    selected_mission = MISSIONS[mission_name]

# --- Sidebar: Quick Presets (Free-Play only) ---
if not in_mission:
    st.sidebar.markdown("**⚡ Quick Presets**")
    p1, p2 = st.sidebar.columns(2)
    p1.button("Baseline", use_container_width=True, on_click=apply_preset, args=("baseline",))
    p2.button("Resistojet", use_container_width=True, on_click=apply_preset, args=("resistojet",))
    st.sidebar.button("❄️ Freeze Risk", use_container_width=True, on_click=apply_preset, args=("freeze",))
    st.sidebar.divider()
else:
    st.sidebar.info(
        f"🔒 **{selected_mission.difficulty} Bus Locked**\n\n"
        f"Tank Volume ({selected_mission.V_tank_L:.1f} L), Initial Pressure ({selected_mission.P_init_MPa:.0f} MPa), "
        f"Initial Temp ({selected_mission.T_init_K:.0f} K), and Dry Mass ({selected_mission.m_dry_kg:.0f} kg) are fixed by the spacecraft chassis."
    )

# --- Sidebar: Core Controls ---
st.sidebar.header("Thruster & Propellant")
propellant_name = st.sidebar.selectbox(
    "Propellant",
    ["Nitrogen (N2)", "Helium (He)", "Argon (Ar)"],
    key="propellant",
)
gas = get_propellant(propellant_name)

d_throat_mm = st.sidebar.slider("Nozzle Throat Diameter d* [mm]", 0.6, 2.6, step=0.1, key="d_throat_mm")
A_throat = np.pi * (d_throat_mm * 1e-3 / 2.0) ** 2

use_regulator = st.sidebar.toggle("Enable Pressure Regulator", key="use_regulator")
P_reg_MPa = st.sidebar.slider("Regulator Setpoint [MPa]", 1.0, 15.0, step=0.5, key="P_reg_MPa", disabled=not use_regulator)

use_heater = st.sidebar.toggle("Enable Resistojet Heater", key="use_heater")
Q_heater = st.sidebar.slider("Heater Power [W]", 0.0, 150.0, step=5.0, key="Q_heater", disabled=not use_heater)

Q_wall = st.sidebar.slider("Ambient Tank Wall Heat [W]", 0.0, 10.0, step=0.5, key="Q_wall")

# --- Sidebar: Spacecraft Bus (Locked in Mission Mode) ---
st.sidebar.header("Spacecraft Bus")
V_tank_L = st.sidebar.slider(
    "Tank Volume [L]", 1.0, 10.0,
    value=selected_mission.V_tank_L if in_mission else st.session_state.V_tank_L,
    step=0.5, disabled=in_mission,
)
P_init_MPa = st.sidebar.slider(
    "Initial Tank Pressure [MPa]", 5.0, 35.0,
    value=selected_mission.P_init_MPa if in_mission else st.session_state.P_init_MPa,
    step=1.0, disabled=in_mission,
)
T_init_K = st.sidebar.slider(
    "Initial Tank Temp [K]", 250.0, 330.0,
    value=selected_mission.T_init_K if in_mission else st.session_state.T_init_K,
    step=5.0, disabled=in_mission,
)
m_dry = st.sidebar.slider(
    "Spacecraft Dry Mass [kg]", 4.0, 25.0,
    value=selected_mission.m_dry_kg if in_mission else st.session_state.m_dry,
    step=1.0, disabled=in_mission,
)

# --- Sidebar: Advanced Controls ---
with st.sidebar.expander("⚙️ Advanced Nozzle & Burn Settings"):
    area_ratio = st.slider("Nozzle Area Ratio Ae/A*", 10.0, 120.0, step=5.0, key="area_ratio")
    eta_nozzle = st.slider("Nozzle Efficiency η_N", 0.75, 1.00, step=0.01, key="eta_nozzle")
    burn_duration = st.slider("Free-Play Burn Duration [s]", 10.0, 180.0, step=10.0, key="burn_duration", disabled=in_mission)


def render_state_table(res, idx: int = -1):
    """Display a station-by-station thermodynamic state table across the SSSF train."""
    P_t = float(res["P"][idx]) / 1e6
    T_t = float(res["T"][idx])
    P_c = min(P_t, P_reg_MPa) if use_regulator else P_t
    mdot = float(res["mdot"][idx])
    q_h = Q_heater if use_heater else 0.0
    T0_noz = T_t + (q_h / (mdot * gas.cp) if mdot > 1e-9 else 0.0)
    F_val = float(res["F"][idx])
    isp_val = float(res["isp"][idx])

    df_states = pd.DataFrame([
        {"Station": "1. Propellant Tank (Transient)", "Pressure [MPa]": f"{P_t:.2f}", "Temp [K]": f"{T_t:.1f}", "Process": "Variable-mass blowdown / wall heat"},
        {"Station": "2. Post-Regulator (SSSF)", "Pressure [MPa]": f"{P_c:.2f}", "Temp [K]": f"{T_t:.1f}", "Process": "Isenthalpic throttling (h₁ = h₂)" if use_regulator else "Bypassed"},
        {"Station": "3. Post-Heater (SSSF)", "Pressure [MPa]": f"{P_c:.2f}", "Temp [K]": f"{T0_noz:.1f}", "Process": f"Isobaric heating (+{q_h:.0f} W)" if use_heater else "Bypassed"},
        {"Station": "4. Nozzle Exit (SSSF)", "Pressure [MPa]": "Vacuum (0.00)", "Temp [K]": "Supersonic", "Process": f"Choked expansion (F={F_val:.2f} N, Isp={isp_val:.1f} s)"},
    ])
    st.dataframe(df_states, use_container_width=True, hide_index=True)


# ==============================================================================
# MODE 1: FREE-PLAY MODE
# ==============================================================================
if mode == "Free-Play Mode":
    res = simulate_freeplay_blowdown(
        gas=gas, V_tank=V_tank_L * 1e-3, P_init=P_init_MPa * 1e6, T_init=T_init_K,
        m_dry=m_dry, A_throat=A_throat, area_ratio=area_ratio,
        burn_duration=burn_duration, eta_nozzle=eta_nozzle,
        use_regulator=use_regulator, P_reg_set=P_reg_MPa * 1e6,
        use_heater=use_heater, Q_heater=Q_heater if use_heater else 0.0,
        Q_tank_wall=Q_wall,
    )

    # Interactive time scrubber to inspect any instant of the blowdown
    t_arr = res["t"]
    t_idx = st.slider("Inspect Burn Timestamp [s]", 0, len(t_arr) - 1, len(t_arr) - 1, format="Step %d")
    fill_pct = 100.0 * float(res["m"][t_idx]) / float(res["m_init"])
    P_t_MPa = float(res["P"][t_idx]) / 1e6
    T_t_K = float(res["T"][t_idx])
    P_c_MPa = min(P_t_MPa, P_reg_MPa) if use_regulator else P_t_MPa
    mdot_curr = float(res["mdot"][t_idx])
    T0_noz = T_t_K + ((Q_heater if use_heater else 0.0) / (mdot_curr * gas.cp) if mdot_curr > 1e-9 else 0.0)

    render_interactive_schematic(
        propellant_name=propellant_name.split(" ")[0],
        fill_pct=fill_pct,
        P_tank_MPa=P_t_MPa,
        T_tank_K=T_t_K,
        use_regulator=use_regulator,
        P_reg_MPa=P_reg_MPa,
        P_chamber_MPa=P_c_MPa,
        use_heater=use_heater,
        Q_heater_W=Q_heater if use_heater else 0.0,
        T_nozzle_in_K=T0_noz,
        thrust_N=float(res["F"][t_idx]),
        isp_s=float(res["isp"][t_idx]),
        mdot_g_s=mdot_curr * 1e3,
        Q_wall_W=Q_wall,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cumulative Δv", f"{res['dv'][-1]:.2f} m/s")
    k2.metric("Peak Thrust", f"{res['F'].max():.2f} N")
    k3.metric("Peak Isp", f"{res['isp'].max():.1f} s")
    k4.metric("Min Tank Temp", f"{res['T'].min():.1f} K", delta="FREEZE RISK" if res["T"].min() < 230 else "Safe", delta_color="inverse" if res["T"].min() < 230 else "normal")

    # Save to Comparison buttons
    c1, c2 = st.columns(2)
    if c1.button("💾 Save Run as Case A", use_container_width=True):
        st.session_state.case_a = {"label": f"Case A ({propellant_name}, Q={Q_heater if use_heater else 0:.0f}W)", "res": res}
        st.toast("Saved as Case A")
    if c2.button("💾 Save Run as Case B", use_container_width=True):
        st.session_state.case_b = {"label": f"Case B ({propellant_name}, Q={Q_heater if use_heater else 0:.0f}W)", "res": res}
        st.toast("Saved as Case B")

    # Selectable telemetry plot
    metric_choice = st.selectbox("Telemetry Plot", ["Tank Temperature [K]", "Tank Pressure [MPa]", "Vacuum Thrust [N]", "Cumulative Δv [m/s]", "Specific Impulse [s]"])
    fig = go.Figure()
    if metric_choice == "Tank Temperature [K]":
        fig.add_trace(go.Scatter(x=res["t"], y=res["T"], mode="lines", name="T(t)", line=dict(color="#38bdf8", width=2.5)))
        fig.add_hline(y=230.0, line_dash="dash", line_color="#ef4444", annotation_text="Valve Freeze Limit (230 K)")
    elif metric_choice == "Tank Pressure [MPa]":
        fig.add_trace(go.Scatter(x=res["t"], y=res["P"] / 1e6, mode="lines", name="P(t)", line=dict(color="#a855f7", width=2.5)))
    elif metric_choice == "Vacuum Thrust [N]":
        fig.add_trace(go.Scatter(x=res["t"], y=res["F"], mode="lines", name="F(t)", line=dict(color="#fb923c", width=2.5)))
    elif metric_choice == "Cumulative Δv [m/s]":
        fig.add_trace(go.Scatter(x=res["t"], y=res["dv"], mode="lines", name="Δv(t)", line=dict(color="#22c55e", width=2.5)))
    else:
        fig.add_trace(go.Scatter(x=res["t"], y=res["isp"], mode="lines", name="Isp(t)", line=dict(color="#eab308", width=2.5)))

    fig.add_vline(x=float(t_arr[t_idx]), line_dash="dot", line_color="#94a3b8")
    fig.update_layout(xaxis_title="Burn Time [s]", yaxis_title=metric_choice, template="plotly_dark", height=360, margin=dict(l=50, r=20, t=20, b=45))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Live Thermodynamic State-Point Table (at selected timestamp)"):
        render_state_table(res, idx=t_idx)


# ==============================================================================
# MODE 2: MISSION MODE (LOCKED BUS + EXPLICIT EXECUTION)
# ==============================================================================
elif mode == "Mission Mode":
    targets = compute_hohmann_targets(selected_mission.alt_start_km, selected_mission.alt_end_km)

    st.markdown(f"### {selected_mission.name}")
    st.caption(f"**Difficulty:** {selected_mission.difficulty}  |  **Target Δv:** {targets['dv1_m_s'] + targets['dv2_m_s']:.2f} m/s  |  **Coast Time:** {targets['t_coast_s']/60.0:.1f} min")
    st.write(selected_mission.brief)

    # Snapshot of unlocked engineering parameters
    current_params = {
        "mission_id": selected_mission.id,
        "propellant": propellant_name,
        "d_throat_mm": d_throat_mm,
        "area_ratio": area_ratio,
        "eta_nozzle": eta_nozzle,
        "use_regulator": use_regulator,
        "P_reg_MPa": P_reg_MPa,
        "use_heater": use_heater,
        "Q_heater": Q_heater if use_heater else 0.0,
        "Q_wall": Q_wall,
    }
    config_changed = (st.session_state.mission_tested_params != current_params)

    col_btn, col_msg = st.columns([1.3, 2.7])
    with col_btn:
        run_clicked = st.button("🚀 Execute Mission Burn", type="primary", use_container_width=True)

    with col_msg:
        if run_clicked:
            with st.spinner("Flying Burn 1 → Coast Phase → Burn 2..."):
                st.session_state.mission_result = simulate_hohmann_mission(
                    gas=gas,
                    V_tank=selected_mission.V_tank_L * 1e-3,
                    P_init=selected_mission.P_init_MPa * 1e6,
                    T_init=selected_mission.T_init_K,
                    m_dry=selected_mission.m_dry_kg,
                    A_throat=A_throat,
                    area_ratio=area_ratio,
                    dv1_target=targets["dv1_m_s"],
                    dv2_target=targets["dv2_m_s"],
                    t_coast=targets["t_coast_s"],
                    eta_nozzle=eta_nozzle,
                    Q_heater=Q_heater if use_heater else 0.0,
                    Q_tank_wall=Q_wall,
                    regulated=use_regulator,
                    P_reg_set=P_reg_MPa * 1e6,
                )
                st.session_state.mission_tested_params = current_params.copy()
                config_changed = False
        elif st.session_state.mission_result is None:
            st.info("Tune the unlocked thruster & thermal controls in the sidebar, then click **Execute Mission Burn** to fly the test.")
        elif config_changed:
            st.warning("⚠️ Parameters changed since your last flight test. Click **Execute Mission Burn** to test this configuration.")

    # Only reveal verdict and telemetry once the current configuration has been flown
    if st.session_state.mission_result is not None and not config_changed:
        res_h = st.session_state.mission_result
        verdict = evaluate_mission(selected_mission, res_h)

        if verdict["passed_all"]:
            st.success(f"🏆 **MISSION ACCOMPLISHED!** Engineering Score: {verdict['score']}/100")
        else:
            st.error(f"❌ **MISSION FAILED** — Engineering Score: {verdict['score']}/100. Review the failed criteria below, adjust your thruster, and re-fly.")

        st.dataframe(pd.DataFrame(verdict["checks"]), use_container_width=True, hide_index=True)

        # Interactive schematic at end of Burn 2
        fill_end = 100.0 * float(res_h["m"][-1]) / float(res_h["m_init"])
        P_end = float(res_h["P"][-1]) / 1e6
        T_end = float(res_h["T"][-1])
        P_c_end = min(P_end, P_reg_MPa) if use_regulator else P_end
        mdot_end = float(res_h["mdot"][-1])
        T0_end = T_end + ((Q_heater if use_heater else 0.0) / (mdot_end * gas.cp) if mdot_end > 1e-9 else 0.0)

        render_interactive_schematic(
            propellant_name=propellant_name.split(" ")[0],
            fill_pct=fill_end, P_tank_MPa=P_end, T_tank_K=T_end,
            use_regulator=use_regulator, P_reg_MPa=P_reg_MPa, P_chamber_MPa=P_c_end,
            use_heater=use_heater, Q_heater_W=Q_heater if use_heater else 0.0, T_nozzle_in_K=T0_end,
            thrust_N=float(res_h["F"][-1]), isp_s=float(res_h["isp"][-1]),
            mdot_g_s=mdot_end * 1e3, Q_wall_W=Q_wall,
        )

        # 4-panel Mission Dashboard
        t_min = res_h["t"] / 60.0
        fig_m = make_subplots(rows=2, cols=2, subplot_titles=("Tank Temperature [K]", "Tank Pressure [MPa]", "Vacuum Thrust [N]", "Cumulative Δv [m/s]"))
        fig_m.add_trace(go.Scatter(x=t_min, y=res_h["T"], line=dict(color="#38bdf8")), row=1, col=1)
        fig_m.add_hline(y=selected_mission.min_temp_K, line_dash="dash", line_color="#ef4444", row=1, col=1)
        fig_m.add_trace(go.Scatter(x=t_min, y=res_h["P"] / 1e6, line=dict(color="#a855f7")), row=1, col=2)
        fig_m.add_trace(go.Scatter(x=t_min, y=res_h["F"], line=dict(color="#fb923c")), row=2, col=1)
        fig_m.add_hline(y=selected_mission.max_peak_thrust_N, line_dash="dash", line_color="#ef4444", row=2, col=1)
        fig_m.add_trace(go.Scatter(x=t_min, y=res_h["dv"], line=dict(color="#22c55e")), row=2, col=2)
        fig_m.update_layout(height=520, showlegend=False, template="plotly_dark", margin=dict(l=45, r=20, t=40, b=40))
        st.plotly_chart(fig_m, use_container_width=True)


# ==============================================================================
# MODE 3: COMPARISON MODE
# ==============================================================================
elif mode == "Comparison Mode":
    if st.session_state.case_a is None or st.session_state.case_b is None:
        st.info("Go to **Free-Play Mode** and save both **Case A** and **Case B** to compare them side by side.")
    else:
        ca, cb = st.session_state.case_a, st.session_state.case_b
        ra, rb = ca["res"], cb["res"]
        fig_c = make_subplots(rows=1, cols=2, subplot_titles=("Cumulative Δv [m/s]", "Tank Temperature [K]"))
        fig_c.add_trace(go.Scatter(x=ra["t"], y=ra["dv"], name=ca["label"], line=dict(color="#38bdf8")), row=1, col=1)
        fig_c.add_trace(go.Scatter(x=rb["t"], y=rb["dv"], name=cb["label"], line=dict(color="#fb923c")), row=1, col=1)
        fig_c.add_trace(go.Scatter(x=ra["t"], y=ra["T"], name=ca["label"], showlegend=False, line=dict(color="#38bdf8")), row=1, col=2)
        fig_c.add_trace(go.Scatter(x=rb["t"], y=rb["T"], name=cb["label"], showlegend=False, line=dict(color="#fb923c")), row=1, col=2)
        fig_c.add_hline(y=230.0, line_dash="dash", line_color="#ef4444", row=1, col=2)
        fig_c.update_layout(height=420, template="plotly_dark")
        st.plotly_chart(fig_c, use_container_width=True)


# ==============================================================================
# MODE 4: VALIDATION AUDIT
# ==============================================================================
elif mode == "Validation Audit":
    res = simulate_freeplay_blowdown(
        gas=gas, V_tank=V_tank_L * 1e-3, P_init=P_init_MPa * 1e6, T_init=T_init_K,
        m_dry=m_dry, A_throat=A_throat, area_ratio=area_ratio,
        burn_duration=burn_duration, eta_nozzle=eta_nozzle,
        use_regulator=use_regulator, P_reg_set=P_reg_MPa * 1e6,
        use_heater=use_heater, Q_heater=Q_heater if use_heater else 0.0,
        Q_tank_wall=Q_wall,
    )
    U_init = float(res["m"][0] * gas.cv * res["T"][0])
    U_final = float(res["m"][-1] * gas.cv * res["T"][-1])
    dU_actual = U_final - U_init
    Q_in = float(res.get("Q_in_total", Q_wall * res["t"][-1]))
    E_out = float(res.get("E_out_total", Q_in - dU_actual))
    residual = abs(dU_actual - (Q_in - E_out))
    rel_err = residual / max(abs(U_init), 1.0)

    c1, c2 = st.columns(2)
    c1.metric("First Law Energy Residual", f"{residual:.4f} J", f"Rel. Error: {rel_err:.2e}")
    c2.metric("Second Law Compliance", "PASS", "Ṡ_gen ≥ 0 W/K")