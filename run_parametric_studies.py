import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from thermo_engine.fluid_props import get_propellant
from thermo_engine.hohmann import compute_hohmann_targets
from thermo_engine.tank_transient import simulate_freeplay_blowdown, simulate_hohmann_mission

os.makedirs("report_figures", exist_ok=True)

# --- Archival Engineering Plot Styling (Matches Sample Report) ---
plt.rcParams.update({
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.size": 10.5,
    "axes.labelsize": 11,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#cccccc",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "legend.frameon": True,
    "legend.facecolor": "white",
    "legend.edgecolor": "#333333",
    "legend.fancybox": False,
    "legend.framealpha": 1.0,
    "legend.fontsize": 9.5,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "figure.dpi": 150,
})

COLORS = ["#003f5c", "#bc5090", "#ef5675", "#ff764a", "#ffa600"]
ANNOTATION_BOX = dict(boxstyle="square,pad=0.35", facecolor="white", edgecolor="#333333", linewidth=0.8)

# Baseline Reference Parameters
V_TANK = 4.0e-3        # 4.0 L
P_INIT = 20.0e6        # 20 MPa
T_INIT = 295.0         # 295 K
M_DRY = 12.0           # 12 kg
D_THROAT = 1.4e-3      # 1.4 mm
A_THROAT = np.pi * (D_THROAT / 2.0) ** 2
AREA_RATIO = 50.0
ETA_N = 0.92
TARGETS = compute_hohmann_targets(400.0, 450.0)


def save_fig(fig: plt.Figure, filename: str):
    path = os.path.join("report_figures", f"{filename}.png")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ==============================================================================
# STUDY 1: Resistojet Heater Power Sweep (0 W to 100 W) — Report Figure 2
# ==============================================================================
print("\n=== STUDY 1: RESISTOJET HEATER POWER SWEEP (N2, 90s Free-Play) ===")
gas_n2 = get_propellant("Nitrogen (N2)")
powers = [0.0, 25.0, 50.0, 75.0, 100.0]
rows_s1 = []

fig1, ax1 = plt.subplots(figsize=(7.2, 4.4))
axins = ax1.inset_axes([0.46, 0.14, 0.48, 0.46])  # [x0, y0, width, height] in axes fraction

for i, q in enumerate(powers):
    res = simulate_freeplay_blowdown(
        gas=gas_n2, V_tank=V_TANK, P_init=P_INIT, T_init=T_INIT, m_dry=M_DRY,
        A_throat=A_THROAT, area_ratio=AREA_RATIO, burn_duration=90.0,
        eta_nozzle=ETA_N, use_heater=(q > 0), Q_heater=q, Q_tank_wall=0.0,
    )
    rows_s1.append({
        "Heater [W]": q,
        "Final dv [m/s]": round(float(res["dv"][-1]), 2),
        "Peak Isp [s]": round(float(res["isp"].max()), 1),
        "Prop Used [kg]": round(float(res["m_init"] - res["m"][-1]), 4),
        "Min Temp [K]": round(float(res["T"].min()), 1),
    })
    lbl = rf"$\dot{{Q}}_{{\mathrm{{heater}}}} = {q:.0f}$ W"
    ax1.plot(res["t"], res["dv"], color=COLORS[i], linewidth=1.8, label=lbl)
    axins.plot(res["t"], res["dv"], color=COLORS[i], linewidth=1.8)

print(pd.DataFrame(rows_s1).to_string(index=False))
ax1.set_xlabel(r"Burn Time, $t$ [s]")
ax1.set_ylabel(r"Cumulative Velocity Increment, $\Delta v$ [m/s]")
ax1.set_xlim(0, 90)
ax1.set_ylim(0, 48)
ax1.legend(
    loc="lower center", bbox_to_anchor=(0.5, 1.02),
    ncol=5, columnspacing=0.9, handlelength=1.4, fontsize=8.8
)

# Configure zoomed inset
axins.set_xlim(55, 90)
axins.set_ylim(42.5, 44.8)
axins.tick_params(labelsize=8.5)
axins.grid(True, color="#cccccc", linewidth=0.5)

save_fig(fig1, "study1_heater_sweep")


# ==============================================================================
# STUDY 2: Propellant Species Trade-Off (N2 vs. He vs. Ar)
# ==============================================================================
print("\n=== STUDY 2: PROPELLANT SPECIES TRADE-OFF (4 L, 20 MPa, 90s Burn) ===")
species = [("Nitrogen (N2)", r"Nitrogen ($\mathrm{N}_2$)", "#003f5c"),
           ("Helium (He)", r"Helium ($\mathrm{He}$)", "#d62728"),
           ("Argon (Ar)", r"Argon ($\mathrm{Ar}$)", "#2ca02c")]
rows_s2 = []

fig2, ax2 = plt.subplots(figsize=(7.2, 4.2))
for sp_key, sp_lbl, col in species:
    g = get_propellant(sp_key)
    res = simulate_freeplay_blowdown(
        gas=g, V_tank=V_TANK, P_init=P_INIT, T_init=T_INIT, m_dry=M_DRY,
        A_throat=A_THROAT, area_ratio=AREA_RATIO, burn_duration=90.0,
        eta_nozzle=ETA_N, use_heater=False, Q_tank_wall=0.0,
    )
    rows_s2.append({
        "Propellant": sp_key,
        "Init Mass [kg]": round(float(res["m_init"]), 4),
        "Final dv [m/s]": round(float(res["dv"][-1]), 2),
        "Peak Isp [s]": round(float(res["isp"].max()), 1),
        "Min Temp [K]": round(float(res["T"].min()), 1),
    })
    ax2.plot(res["t"], res["isp"], color=col, linewidth=1.8, label=sp_lbl)

print(pd.DataFrame(rows_s2).to_string(index=False))
ax2.set_xlabel(r"Burn Time, $t$ [s]")
ax2.set_ylabel(r"Specific Impulse, $I_{sp}$ [s]")
ax2.set_xlim(0, 90)
ax2.set_ylim(bottom=0)
ax2.legend(loc="upper right")
save_fig(fig2, "study2_propellant_tradeoff")


# ==============================================================================
# STUDY 3: Unregulated Blowdown vs. Pressure-Regulated Thrust Profiles
# ==============================================================================
print("\n=== STUDY 3: BLOWDOWN VS. REGULATED OPERATION (N2, 90s Burn) ===")
reg_cases = [
    ("Blowdown (Unregulated)", False, 5.0e6, "#1f77b4", "-"),
    ("Regulated (8.0 MPa)", True, 8.0e6, "#d62728", "--"),
    ("Regulated (5.0 MPa)", True, 5.0e6, "#2ca02c", "-."),
    ("Regulated (3.0 MPa)", True, 3.0e6, "#ff7f0e", ":"),
]
rows_s3 = []

fig3, ax3 = plt.subplots(figsize=(7.2, 4.2))
for label, use_reg, p_set, col, ls in reg_cases:
    res = simulate_freeplay_blowdown(
        gas=gas_n2, V_tank=V_TANK, P_init=P_INIT, T_init=T_INIT, m_dry=M_DRY,
        A_throat=A_THROAT, area_ratio=AREA_RATIO, burn_duration=90.0,
        eta_nozzle=ETA_N, use_regulator=use_reg, P_reg_set=p_set,
    )
    rows_s3.append({
        "Mode": label,
        "Peak Thrust [N]": round(float(res["F"].max()), 2),
        "Final Thrust [N]": round(float(res["F"][-1]), 2),
        "Final dv [m/s]": round(float(res["dv"][-1]), 2),
        "Min Temp [K]": round(float(res["T"].min()), 1),
    })
    ax3.plot(res["t"], res["F"], color=col, linestyle=ls, linewidth=1.8, label=label)

print(pd.DataFrame(rows_s3).to_string(index=False))
ax3.set_xlabel(r"Burn Time, $t$ [s]")
ax3.set_ylabel(r"Vacuum Thrust, $F(t)$ [N]")
ax3.set_xlim(0, 90)
ax3.set_ylim(bottom=0)
ax3.legend(loc="upper right")
save_fig(fig3, "study3_regulator_comparison")


# ==============================================================================
# STUDY 4: Nozzle Throat Sizing & Valve Freeze Risk — Report Figure 5
# ==============================================================================
print("\n=== STUDY 4: NOZZLE THROAT SIZING & VALVE FREEZE MARGIN (N2, 90s Burn) ===")
diameters_mm = [0.8, 1.2, 1.6, 2.0, 2.4]
rows_s4 = []

fig4, ax4 = plt.subplots(figsize=(7.2, 4.4))
for i, d_mm in enumerate(diameters_mm):
    A_t = np.pi * (d_mm * 1e-3 / 2.0) ** 2
    res = simulate_freeplay_blowdown(
        gas=gas_n2, V_tank=V_TANK, P_init=P_INIT, T_init=T_INIT, m_dry=M_DRY,
        A_throat=A_t, area_ratio=AREA_RATIO, burn_duration=90.0,
        eta_nozzle=ETA_N, Q_tank_wall=0.0,
    )
    min_T = float(res["T"].min())
    rows_s4.append({
        "Throat d* [mm]": d_mm,
        "Peak Thrust [N]": round(float(res["F"].max()), 2),
        "Final dv [m/s]": round(float(res["dv"][-1]), 2),
        "Min Temp [K]": round(min_T, 1),
        "Valve Freeze (<230K)": "YES" if min_T < 230.0 else "NO",
    })
    ax4.plot(res["t"], res["T"], color=COLORS[i], linewidth=1.8, label=rf"$d^* = {d_mm:.1f}$ mm")

print(pd.DataFrame(rows_s4).to_string(index=False))
ax4.axhline(230.0, color="#d62728", linestyle="--", linewidth=1.2, zorder=2)
ax4.text(
    48.0, 236.0, r"Valve Freeze Limit ($T = 230$ K)",
    color="#d62728", fontsize=9.5, ha="center", va="bottom",
    bbox=dict(boxstyle="square,pad=0.3", facecolor="white", edgecolor="#d62728", linewidth=0.8),
    zorder=5,
)
ax4.set_xlabel(r"Burn Time, $t$ [s]")
ax4.set_ylabel(r"Tank Temperature, $T(t)$ [K]")
ax4.set_xlim(0, 90)
ax4.set_ylim(45, 315)
ax4.legend(loc="upper right", ncol=1)
save_fig(fig4, "study4_throat_freeze_risk")


# ==============================================================================
# STUDY 5: Coast-Phase Thermal Recovery in a Hohmann Transfer — Report Figure 6
# ==============================================================================
print("\n=== STUDY 5: COAST-PHASE THERMAL RECOVERY (400->450 km Hohmann) ===")
wall_heats = [0.0, 1.0, 2.0, 4.0, 6.0]
rows_s5 = []

fig5, ax5 = plt.subplots(figsize=(7.4, 4.6))
t1_min, t2_min = 0.0, 0.0
for i, q_w in enumerate(wall_heats):
    res_h = simulate_hohmann_mission(
        gas=gas_n2, V_tank=V_TANK, P_init=P_INIT, T_init=T_INIT, m_dry=M_DRY,
        A_throat=A_THROAT, area_ratio=AREA_RATIO,
        dv1_target=TARGETS["dv1_m_s"], dv2_target=TARGETS["dv2_m_s"],
        t_coast=TARGETS["t_coast_s"], eta_nozzle=ETA_N,
        Q_heater=25.0, Q_tank_wall=q_w, regulated=False,
    )
    t1_min = res_h["t_burn1_end"] / 60.0
    t2_min = res_h["t_coast_end"] / 60.0
    rows_s5.append({
        "Wall Heat [W]": q_w,
        "Achieved dv [m/s]": round(float(res_h["dv"][-1]), 2),
        "Min Temp [K]": round(float(res_h["T"].min()), 1),
        "Final Temp [K]": round(float(res_h["T"][-1]), 1),
        "Prop Left [%]": round(100.0 * float(res_h["m"][-1]) / float(res_h["m_init"]), 1),
    })
    ax5.plot(res_h["t"] / 60.0, res_h["T"], color=COLORS[i], linewidth=1.8, label=rf"$\dot{{Q}}_{{\mathrm{{wall}}}} = {q_w:.0f}$ W")

print(pd.DataFrame(rows_s5).to_string(index=False))

# Subtle coast-phase shading & boundaries
ax5.axvspan(t1_min, t2_min, color="#f0f4f8", alpha=0.65, zorder=0)
ax5.axvline(t1_min, color="#555555", linestyle=":", linewidth=1.0, zorder=2)
ax5.axvline(t2_min, color="#555555", linestyle=":", linewidth=1.0, zorder=2)

# Freeze limit line + non-overlapping label
ax5.axhline(230.0, color="#d62728", linestyle="--", linewidth=1.2, zorder=2)
ax5.text(
    t2_min * 0.96, 224.0, r"Valve Freeze Limit ($T = 230$ K)",
    color="#d62728", fontsize=9.0, ha="right", va="top",
    bbox=dict(boxstyle="square,pad=0.25", facecolor="white", edgecolor="#d62728", linewidth=0.8),
    zorder=5,
)

# Coast Phase label placed cleanly near top-center of coast window
ax5.text(
    (t1_min + t2_min) * 0.5, 294.0, "Coast Phase (Valve Closed, Thermal Recovery)",
    ha="center", va="top", fontsize=9.2, bbox=ANNOTATION_BOX, zorder=5,
)

ax5.set_xlabel(r"Mission Time, $t$ [min]")
ax5.set_ylabel(r"Tank Temperature, $T(t)$ [K]")
ax5.set_xlim(0, t2_min * 1.04)
ax5.set_ylim(195, 305)
ax5.legend(
    loc="lower center", bbox_to_anchor=(0.5, 1.02),
    ncol=5, columnspacing=0.9, handlelength=1.4, fontsize=8.8
)
save_fig(fig5, "study5_coast_thermal_recovery")
