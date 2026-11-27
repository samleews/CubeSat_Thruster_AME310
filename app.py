import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from thermo_engine.fluid_props import PROPELLANTS, get_propellant
from thermo_engine.hohmann import compute_hohmann_targets
from thermo_engine.tank_transient import simulate_freeplay_blowdown, simulate_hohmann_mission
from thermo_engine.validation import audit_conservation, audit_second_law
from visuals.plots import (
    METRIC_CONFIG,
    plot_energy_balance,
    plot_transient_dashboard,
    plot_comparison_overlay,
)
from visuals.animations import plot_hohmann_animation
from visuals.live_player import render_live_freeplay_player
from game.guided_tour import GUIDED_STEPS
from game.missions import MISSIONS, evaluate_mission

st.set_page_config(page_title="AME 310 — CubeSat Thruster Lab", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
      h1 { font-size: 1.8rem !important; margin-bottom: 0.1rem !important; }
      div[data-testid="stSidebar"] .stButton button { font-size: 0.82rem; padding: 0.3rem 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Default Parameter State ---
DEFAULTS = {
    "active_mode": "Free-Play Mode",
    "tour_step": 0,
    "case_a": None,
    "case_b": None,
    "gas_key": "Nitrogen (N2)",
    "V_tank_L": 4.0,
    "P_init_MPa": 20.0,
    "T_init_K": 295.0,
    "m_dry": 12.0,
    "burn_duration": 90.0,
    "d_throat_mm": 1.4,
    "area_ratio": 50.0,
    "eta_nozzle": 0.92,
    "use_regulator": False,
    "P_reg_MPa": 5.0,
    "use_heater": False,
    "Q_heater": 50.0,
    "Q_tank_wall": 2.0,
    "mission_result": None,
    "mission_cons": None,
    "mission_eval": None,
    "mission_tested_params": None,
    "mission_result_key": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def apply_preset(preset_name: str):
    if preset_name == "baseline":
        st.session_state.update(
            gas_key="Nitrogen (N2)", V_tank_L=4.0, P_init_MPa=20.0, T_init_K=295.0,
            d_throat_mm=1.4, use_regulator=False, use_heater=False, Q_tank_wall=2.0,
        )
    elif preset_name == "resistojet":
        st.session_state.update(
            gas_key="Nitrogen (N2)", V_tank_L=4.0, P_init_MPa=20.0, T_init_K=295.0,
            d_throat_mm=1.4, use_regulator=True, P_reg_MPa=5.0, use_heater=True, Q_heater=60.0, Q_tank_wall=2.0,
        )
    elif preset_name == "freeze":
        st.session_state.update(
            gas_key="Nitrogen (N2)", V_tank_L=3.0, P_init_MPa=22.0, T_init_K=285.0,
            d_throat_mm=2.0, use_regulator=False, use_heater=False, Q_tank_wall=0.0,
        )


# --- Header & Pill-Style Top Navigation ---
st.title("CubeSat Cold-Gas & Resistojet Thruster Virtual Lab")

MODES = ["Free-Play Mode", "Mission Mode", "Comparison Mode", "Validation Audit"]
if hasattr(st, "segmented_control"):
    selected = st.segmented_control(
        "Navigation", MODES, default=st.session_state.active_mode, label_visibility="collapsed"
    )
    if selected is not None:
        st.session_state.active_mode = selected
    mode = st.session_state.active_mode
else:
    mode = st.radio("Navigation", MODES, horizontal=True, label_visibility="collapsed")
    st.session_state.active_mode = mode

st.markdown("---")

in_mission = (mode == "Mission Mode")
mission_key = None
m_cfg = None
if in_mission:
    mission_key = st.selectbox("Select Engineering Mission", list(MISSIONS.keys()))
    m_cfg = MISSIONS[mission_key]

# --- Sidebar: Quick Presets (hidden in Mission Mode so bus stays locked) ---
if not in_mission:
    st.sidebar.markdown("**Presets**")
    p1, p2 = st.sidebar.columns(2)
    p1.button("Baseline", use_container_width=True, on_click=apply_preset, args=("baseline",))
    p2.button("Resistojet", use_container_width=True, on_click=apply_preset, args=("resistojet",))
    st.sidebar.button("Freeze Risk", use_container_width=True, on_click=apply_preset, args=("freeze",))
    st.sidebar.markdown("---")
else:
    st.sidebar.info(
        f"🔒 **Mission Bus Locked**\n\n"
        f"Tank Volume ({m_cfg['V_tank_L']:.1f} L), Initial Pressure ({m_cfg['P_init_MPa']:.0f} MPa), "
        f"Initial Temp ({m_cfg['T_init_K']:.0f} K), Dry Mass ({m_cfg['m_dry']:.0f} kg), and Nozzle Efficiency ({m_cfg['eta_nozzle']:.2f}) are fixed by the CubeSat chassis."
    )

# --- Sidebar: Core Controls (Always Visible) ---
with st.sidebar.expander("Core Controls", expanded=True):
    burn_duration = st.slider(
        "Max Burn Duration [s]", 10.0, 300.0, key="burn_duration", step=10.0, disabled=in_mission
    )

    use_regulator = st.toggle("Enable Pressure Regulator", key="use_regulator")
    if use_regulator:
        P_reg_MPa = st.slider("Regulator Setpoint [MPa]", 0.5, 15.0, key="P_reg_MPa", step=0.5)
    else:
        P_reg_MPa = st.session_state.P_reg_MPa

    use_heater = st.toggle("Enable Resistojet Heater", key="use_heater")
    if use_heater:
        Q_heater_val = st.slider("Heater Power [W]", 5.0, 100.0, key="Q_heater", step=5.0)
    else:
        Q_heater_val = st.session_state.Q_heater

# --- Sidebar: Spacecraft Bus (Collapsed by Default, Locked in Mission Mode) ---
with st.sidebar.expander("🛰️ Spacecraft Bus", expanded=False):
    P_init_MPa = st.slider(
        "Initial Tank Pressure P₀ [MPa]", 5.0, 35.0,
        value=m_cfg["P_init_MPa"] if in_mission else st.session_state.P_init_MPa,
        step=1.0, disabled=in_mission,
    )
    V_tank_L = st.slider(
        "Tank Volume [L]", 1.0, 10.0,
        value=m_cfg["V_tank_L"] if in_mission else st.session_state.V_tank_L,
        step=0.5, disabled=in_mission,
    )
    T_init_K = st.slider(
        "Initial Tank Temp T₀ [K]", 260.0, 330.0,
        value=m_cfg["T_init_K"] if in_mission else st.session_state.T_init_K,
        step=5.0, disabled=in_mission,
    )
    m_dry = st.slider(
        "CubeSat Dry Mass [kg]", 4.0, 30.0,
        value=m_cfg["m_dry"] if in_mission else st.session_state.m_dry,
        step=1.0, disabled=in_mission,
    )
    if not in_mission:
        st.session_state.P_init_MPa = P_init_MPa
        st.session_state.V_tank_L = V_tank_L
        st.session_state.T_init_K = T_init_K
        st.session_state.m_dry = m_dry

# --- Sidebar: Pre-Collapsed Advanced Sections ---
with st.sidebar.expander("🧪 Propellant & Thermal Properties", expanded=False):
    gas_key = st.selectbox("Propellant Gas", list(PROPELLANTS.keys()), key="gas_key")
    Q_tank_wall = st.slider("Ambient Tank Wall Heating [W]", 0.0, 10.0, key="Q_tank_wall", step=0.5)

with st.sidebar.expander("🚀 Nozzle Geometry", expanded=False):
    d_throat_mm = st.slider("Nozzle Throat Diameter [mm]", 0.6, 3.0, key="d_throat_mm", step=0.1)
    area_ratio = st.slider("Expansion Ratio (Ae/A*)", 5.0, 100.0, key="area_ratio", step=5.0)
    eta_nozzle = st.slider(
        r"Nozzle Efficiency $\eta_N$", 0.70, 1.00,
        value=m_cfg["eta_nozzle"] if in_mission else st.session_state.eta_nozzle,
        step=0.01,
        disabled=in_mission,
    )
    if not in_mission:
        st.session_state.eta_nozzle = eta_nozzle

Q_heater = Q_heater_val if use_heater else 0.0
gas = get_propellant(gas_key)
A_throat = np.pi * (d_throat_mm * 1e-3 / 2.0) ** 2


def run_freeplay():
    return simulate_freeplay_blowdown(
        gas=gas,
        V_tank=V_tank_L * 1e-3,
        P_init=P_init_MPa * 1e6,
        T_init=T_init_K,
        m_dry=m_dry,
        A_throat=A_throat,
        area_ratio=area_ratio,
        burn_duration=burn_duration,
        eta_nozzle=eta_nozzle,
        use_heater=use_heater,
        Q_heater=Q_heater,
        Q_tank_wall=Q_tank_wall,
        use_regulator=use_regulator,
        P_reg_set=P_reg_MPa * 1e6,
        n_frames=140,
    )


# ==========================================
# 1. FREE-PLAY MODE
# ==========================================
if mode == "Free-Play Mode":
    res = run_freeplay()

    top_l, top_r1, top_r2 = st.columns([2.4, 1.0, 1.0])
    guided_on = top_l.toggle("🧭 Guided Component Walkthrough", value=True)

    run_label = f"{gas.formula} | {P_init_MPa:.0f} MPa | {'Reg' if use_regulator else 'Blow'} | Q={Q_heater:.0f}W"
    if top_r1.button("💾 Save as Case A", use_container_width=True):
        st.session_state.case_a = {"label": run_label, "res": res, "gas": gas}
        st.toast(f"Saved Case A: {run_label}")
    if top_r2.button("💾 Save as Case B", use_container_width=True):
        st.session_state.case_b = {"label": run_label, "res": res, "gas": gas}
        st.toast(f"Saved Case B: {run_label}")

    if guided_on:
        idx = st.session_state.tour_step
        step = GUIDED_STEPS[idx]
        cfg = {
            "gas_key": gas_key,
            "use_regulator": use_regulator,
            "use_heater": use_heater,
            "Q_heater": Q_heater,
            "d_throat_mm": d_throat_mm,
            "min_T": float(res["T"].min()),
            "has_case_a": st.session_state.case_a is not None,
            "has_case_b": st.session_state.case_b is not None,
        }
        completed = step["check"](cfg)

        with st.container(border=True):
            h_col, nav_col = st.columns([3.5, 1.2])
            h_col.markdown(f"#### {step['title']}")
            n1, n2 = nav_col.columns(2)
            if n1.button("◀ Prev", use_container_width=True, disabled=(idx == 0)):
                st.session_state.tour_step -= 1
                st.rerun()
            if n2.button("Next ▶", use_container_width=True, disabled=(idx == len(GUIDED_STEPS) - 1)):
                st.session_state.tour_step += 1
                st.rerun()

            st.progress((idx + 1) / len(GUIDED_STEPS))
            st.markdown(step["summary"])

            # Component Deep Dive with rendered LaTeX equations & live state
            with st.expander(f"🔬 Component Deep Dive: {step['component_name']}", expanded=True):
                st.caption(f"**Control Volume:** {step['cv_type']}")
                st.latex(step["equation"])
                st.markdown(step["physics"])
                st.markdown(f"**Live State:** {step['live_metrics'](res, cfg)}")

            if completed:
                st.success(f"✅ **Setup Ready!** {step['prompt']}")
            else:
                st.info(f"🎯 **Try This:** {step['prompt']}\n\n*Hint: {step['hint']}*")

    html_player = render_live_freeplay_player(
        res=res,
        gas_name=gas.name,
        use_regulator=use_regulator,
        use_heater=use_heater,
        Q_heater=Q_heater,
        burn_duration=burn_duration,
    )
    components.html(html_player, height=665)

# ==========================================
# 2. MISSION MODE (HOHMANN TRANSFER)
# ==========================================
elif mode == "Mission Mode":
    targets = compute_hohmann_targets(m_cfg["alt1_km"], m_cfg["alt2_km"])
    c_req = m_cfg["constraints"]

    # Upfront Mission Briefing & Specific Pass Criteria (visible BEFORE executing)
    st.info(
        f"**Mission Briefing:** {m_cfg['briefing']}\n\n"
        f"**Orbital Targets:** Burn 1 = `{targets['dv1_m_s']:.2f} m/s`  |  "
        f"Coast = `{targets['t_coast_s']/60:.1f} min`  |  "
        f"Burn 2 = `{targets['dv2_m_s']:.2f} m/s`  |  "
        f"Total Δv = `{targets['dv_total_m_s']:.2f} m/s`\n\n"
        f"**Required Pass Criteria:**\n"
        f"- **Target Δv:** ≥ `{0.99 * targets['dv_total_m_s']:.2f} m/s` (99% of target)\n"
        f"- **Valve Freeze Guard:** Min Tank Temp ≥ `{c_req['min_T_K']:.0f} K`\n"
        f"- **Propellant Reserve:** ≥ `{c_req['min_prop_margin_pct']:.0f}%` remaining\n"
        f"- **Heater Power Budget:** ≤ `{c_req['max_heater_W']:.0f} W`\n"
        f"- **First Law Conservation:** Relative Error `< 1e-5`"
    )

    current_params = {
        "mission_key": mission_key,
        "gas_key": gas_key,
        "d_throat_mm": d_throat_mm,
        "area_ratio": area_ratio,
        "eta_nozzle": eta_nozzle,
        "use_regulator": use_regulator,
        "P_reg_MPa": P_reg_MPa,
        "use_heater": use_heater,
        "Q_heater": Q_heater,
        "Q_tank_wall": Q_tank_wall,
    }
    has_prior_for_mission = (
        st.session_state.mission_result is not None
        and st.session_state.mission_result_key == mission_key
    )
    config_changed = (st.session_state.mission_tested_params != current_params)

    col_btn, col_msg = st.columns([1.3, 2.7])
    with col_btn:
        run_clicked = st.button("🚀 Execute Mission Burn", type="primary", use_container_width=True)

    with col_msg:
        if run_clicked:
            with st.spinner("Executing Burn 1 → Coast Phase → Burn 2..."):
                res_m = simulate_hohmann_mission(
                    gas=gas,
                    V_tank=m_cfg["V_tank_L"] * 1e-3,
                    P_init=m_cfg["P_init_MPa"] * 1e6,
                    T_init=m_cfg["T_init_K"],
                    m_dry=m_cfg["m_dry"],
                    A_throat=A_throat,
                    area_ratio=area_ratio,
                    dv1_target=targets["dv1_m_s"],
                    dv2_target=targets["dv2_m_s"],
                    t_coast=targets["t_coast_s"],
                    eta_nozzle=eta_nozzle,
                    Q_heater=Q_heater,
                    Q_tank_wall=Q_tank_wall,
                    regulated=use_regulator,
                    P_reg_set=P_reg_MPa * 1e6,
                )
                cons_m = audit_conservation(res_m, gas)
                ev = evaluate_mission(mission_key, res_m, targets, Q_heater, cons_m)
                st.session_state.mission_result = res_m
                st.session_state.mission_cons = cons_m
                st.session_state.mission_eval = ev
                st.session_state.mission_tested_params = current_params.copy()
                st.session_state.mission_result_key = mission_key
                has_prior_for_mission = True
                config_changed = False
        elif not has_prior_for_mission:
            st.warning("Tune your unlocked thruster & thermal controls in the sidebar, then click **Execute Mission Burn** to fly the test.")
        elif config_changed:
            st.warning("⚠️ Showing your **previous attempt** below (unupdated). Click **Execute Mission Burn** to test your new sidebar settings.")

    # Keep previous attempt data visible (unupdated) until Execute Mission Burn is clicked
    if has_prior_for_mission:
        res_m = st.session_state.mission_result
        ev = st.session_state.mission_eval

        # 1. Hohmann Transfer Animation FIRST
        st.subheader("Orbital Transfer Playback (Burn 1 → Coast → Burn 2)")
        st.plotly_chart(plot_hohmann_animation(targets, res_m), use_container_width=True)

        st.markdown("---")

        # 2. Mission Verdict & Engineering Results
        if ev["passed_all"]:
            st.success(f"🏆 **MISSION ACCOMPLISHED!** Engineering Score: **{ev['score']} / 100**")
        else:
            st.error(f"❌ **MISSION FAILED** — Adjust your sidebar propulsion parameters and re-fly. (Score: {ev['score']} / 100)")

        col_check, col_metrics = st.columns([1.6, 1.0])
        with col_check:
            st.subheader("Engineering Criteria Checklist")
            for label, ok, detail in ev["checks"]:
                icon = "✅" if ok else "❌"
                st.markdown(f"{icon} **{label}** — `{detail}`")
        with col_metrics:
            st.subheader("Burn Summary")
            st.metric("Burn 1 Duration", f"{res_m['t_burn1_end']:.1f} s")
            st.metric("Burn 2 Duration", f"{res_m['t_burn2_end'] - res_m['t_coast_end']:.1f} s")
            st.metric("Peak Specific Impulse", f"{res_m['isp'].max():.1f} s")

        st.plotly_chart(plot_transient_dashboard(res_m), use_container_width=True)

# ==========================================
# 3. COMPARISON MODE
# ==========================================
elif mode == "Comparison Mode":
    st.subheader("Side-by-Side Simulation Comparison (Case A vs. Case B)")
    if st.session_state.case_a is None or st.session_state.case_b is None:
        st.warning(
            "Go to **Free-Play Mode**, configure a run, and click **💾 Save as Case A**. "
            "Then change your settings (or click a **Quick Preset**) and click **💾 Save as Case B**."
        )
    else:
        ca, cb = st.session_state.case_a, st.session_state.case_b
        ra, rb = ca["res"], cb["res"]

        rows = [
            ("Total Created Δv [m/s]", ra["dv"][-1], rb["dv"][-1]),
            ("Propellant Used [kg]", ra["m_init"] - ra["m"][-1], rb["m_init"] - rb["m"][-1]),
            ("Min Tank Temperature [K]", ra["T"].min(), rb["T"].min()),
            ("Final Tank Pressure [MPa]", ra["P"][-1] / 1e6, rb["P"][-1] / 1e6),
            ("Peak Thrust [N]", ra["F"].max(), rb["F"].max()),
            ("Peak Specific Impulse [s]", ra["isp"].max(), rb["isp"].max()),
        ]
        df = pd.DataFrame(
            [
                {
                    "Metric": name,
                    f"Case A ({ca['label']})": round(va, 3),
                    f"Case B ({cb['label']})": round(vb, 3),
                    "Difference (B - A)": round(vb - va, 3),
                }
                for name, va, vb in rows
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        comp_metric = st.selectbox("Select Parameter to Overlay", list(METRIC_CONFIG.keys()))
        st.plotly_chart(plot_comparison_overlay(ca, cb, comp_metric), use_container_width=True)

# ==========================================
# 4. VALIDATION AUDIT
# ==========================================
elif mode == "Validation Audit":
    res = run_freeplay()
    cons = audit_conservation(res, gas)
    sec = audit_second_law(
        res, gas, A_throat, area_ratio, eta_nozzle,
        Q_heater, use_regulator, P_reg_MPa * 1e6
    )
    st.subheader("Quantitative Conservation & Second Law Verification (Current Free-Play Run)")
    v1, v2, v3 = st.columns(3)
    v1.metric("First Law Energy Rel. Error", f"{cons['energy_rel_err']:.2e}", "PASS" if cons["passed"] else "FAIL")
    v2.metric("Energy Residual", f"{cons['energy_residual_J']:.4f} J")
    v3.metric("Min Nozzle S_gen", f"{sec['min_S_gen_W_K']:.4f} W/K", "PASS" if sec["passed"] else "FAIL")
    st.plotly_chart(plot_energy_balance(cons), use_container_width=True)