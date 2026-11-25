import numpy as np
import plotly.graph_objects as go

def plot_hohmann_animation(targets: dict, res: dict) -> go.Figure:
    """Animated 2D Hohmann transfer orbit with burn plume indicators."""
    # Exaggerate altitude difference slightly for clear visual separation
    r_earth_vis = 1.0
    r1_vis = 1.35
    r2_vis = 1.85
    a_vis = 0.5 * (r1_vis + r2_vis)
    c_vis = a_vis - r1_vis
    b_vis = np.sqrt(a_vis**2 - c_vis**2)

    theta = np.linspace(0, 2 * np.pi, 200)
    x_earth, y_earth = r_earth_vis * np.cos(theta), r_earth_vis * np.sin(theta)
    x_orb1, y_orb1 = r1_vis * np.cos(theta), r1_vis * np.sin(theta)
    x_orb2, y_orb2 = r2_vis * np.cos(theta), r2_vis * np.sin(theta)

    # Transfer ellipse (perigee at +x, apogee at -x)
    phi_half = np.linspace(0, np.pi, 100)
    x_trans = a_vis * np.cos(phi_half) - c_vis
    y_trans = b_vis * np.sin(phi_half)

    # Build 40 animation frames: Burn 1 (0..7), Coast (8..31), Burn 2 (32..39)
    n_b1, n_coast, n_b2 = 8, 24, 8
    xs, ys, colors, sizes, labels = [], [], [], [], []

    # Burn 1 arc near perigee
    for ang in np.linspace(-0.12, 0.08, n_b1):
        xs.append(r1_vis * np.cos(ang))
        ys.append(r1_vis * np.sin(ang))
        colors.append("#ef4444")
        sizes.append(16)
        labels.append("BURN 1 (Perigee Kick - SSSF + Transient)")

    # Coast along transfer ellipse
    for ang in np.linspace(0.08, np.pi - 0.08, n_coast):
        xs.append(a_vis * np.cos(ang) - c_vis)
        ys.append(b_vis * np.sin(ang))
        colors.append("#38bdf8")
        sizes.append(12)
        labels.append("COAST PHASE (Valve Closed - Thermal Recovery)")

    # Burn 2 arc near apogee
    achieved_ratio = res["dv"][-1] / max(1e-6, targets["dv_total_m_s"])
    r_final_vis = r1_vis + (r2_vis - r1_vis) * min(1.15, achieved_ratio)
    for ang in np.linspace(np.pi - 0.08, np.pi + 0.14, n_b2):
        xs.append(r_final_vis * np.cos(ang))
        ys.append(r_final_vis * np.sin(ang))
        colors.append("#f97316")
        sizes.append(16)
        labels.append("BURN 2 (Apogee Circularization - SSSF + Transient)")

    frames = [
        go.Frame(
            data=[
                go.Scatter(
                    x=[xs[k]], y=[ys[k]],
                    mode="markers+text",
                    marker=dict(size=sizes[k], color=colors[k], line=dict(width=2, color="white")),
                    text=["CubeSat"],
                    textposition="top center",
                )
            ],
            layout=go.Layout(title_text=f"Hohmann Transfer — {labels[k]}"),
            traces=[4],
        )
        for k in range(len(xs))
    ]

    fig = go.Figure(
        data=[
            go.Scatter(x=x_earth, y=y_earth, fill="toself", fillcolor="#1d4ed8", line=dict(color="#60a5fa"), name="Earth"),
            go.Scatter(x=x_orb1, y=y_orb1, mode="lines", line=dict(color="#94a3b8", dash="dot"), name="Initial Orbit (r₁)"),
            go.Scatter(x=x_orb2, y=y_orb2, mode="lines", line=dict(color="#4ade80", dash="dash"), name="Target Orbit (r₂)"),
            go.Scatter(x=x_trans, y=y_trans, mode="lines", line=dict(color="#facc15", width=2), name="Transfer Ellipse"),
            go.Scatter(
                x=[xs[0]], y=[ys[0]],
                mode="markers+text",
                marker=dict(size=sizes[0], color=colors[0], line=dict(width=2, color="white")),
                text=["CubeSat"],
                textposition="top center",
                name="Spacecraft",
            ),
        ],
        frames=frames,
    )

    fig.update_layout(
        title="Hohmann Transfer — Click Play to Animate",
        template="plotly_dark",
        height=440,
        xaxis=dict(range=[-2.3, 2.3], showgrid=False, zeroline=False, visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(range=[-2.1, 2.1], showgrid=False, zeroline=False, visible=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.02, y=1.08,
                buttons=[
                    dict(label="▶ Play Transfer", method="animate", args=[None, {"frame": {"duration": 110, "redraw": True}, "fromcurrent": True}]),
                    dict(label="⏸ Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]),
                ],
            )
        ],
    )
    return fig


def render_system_schematic(
    m_curr: float,
    m_init: float,
    P_curr_MPa: float,
    T_curr_K: float,
    F_curr_N: float,
    gas_name: str,
    use_regulator: bool,
    use_heater: bool,
    Q_heater: float,
    is_firing: bool,
) -> str:
    """Live HTML/SVG cutaway showing Tank -> [Optional Regulator] -> [Optional Heater] -> Nozzle."""
    fill_pct = max(2.0, min(100.0, 100.0 * (m_curr / max(1e-9, m_init))))
    tank_color = "#ef4444" if T_curr_K < 230.0 else "#38bdf8"
    plume_opacity = 0.65 if (is_firing and F_curr_N > 0.01) else 0.0

    reg_svg = (
        '<rect x="305" y="68" width="100" height="50" rx="6" fill="#1e293b" stroke="#38bdf8" stroke-width="2.5"/>'
        '<text x="355" y="90" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">REGULATOR</text>'
        '<text x="355" y="106" fill="#38bdf8" font-size="10" text-anchor="middle">ACTIVE</text>'
        if use_regulator
        else '<line x1="305" y1="93" x2="405" y2="93" stroke="#64748b" stroke-width="6"/>'
             '<text x="355" y="122" fill="#64748b" font-size="10" text-anchor="middle">Regulator Off</text>'
    )

    heater_svg = (
        f'<rect x="435" y="68" width="105" height="50" rx="6" fill="#1e293b" stroke="#f97316" stroke-width="2.5"/>'
        f'<text x="487" y="90" fill="#f8fafc" font-size="11" font-weight="bold" text-anchor="middle">HEATER</text>'
        f'<text x="487" y="106" fill="#f97316" font-size="10" text-anchor="middle">Q = {Q_heater:.0f} W</text>'
        if use_heater
        else '<line x1="435" y1="93" x2="540" y2="93" stroke="#64748b" stroke-width="6"/>'
             '<text x="487" y="122" fill="#64748b" font-size="10" text-anchor="middle">Heater Off</text>'
    )

    return f"""
    <div style="background:#0f172a; border:1px solid #334155; border-radius:10px; padding:12px; text-align:center;">
      <svg viewBox="0 0 720 185" width="100%" height="170" xmlns="http://www.w3.org/2000/svg">
        <rect x="15" y="12" width="245" height="160" rx="10" fill="none" stroke="#38bdf8" stroke-dasharray="6,4" stroke-width="2"/>
        <text x="137" y="31" fill="#38bdf8" font-size="12" font-weight="bold" text-anchor="middle">TRANSIENT TANK</text>

        <rect x="45" y="45" width="185" height="90" rx="35" fill="#1e293b" stroke="{tank_color}" stroke-width="3"/>
        <rect x="52" y="52" width="{1.71 * fill_pct:.1f}" height="76" rx="28" fill="{tank_color}" opacity="0.4"/>
        <text x="137" y="83" fill="#f8fafc" font-size="13" font-weight="bold" text-anchor="middle">{gas_name} ({fill_pct:.0f}%)</text>
        <text x="137" y="103" fill="#cbd5e1" font-size="11" text-anchor="middle">{P_curr_MPa:.1f} MPa | {T_curr_K:.0f} K</text>

        <line x1="230" y1="93" x2="305" y2="93" stroke="#94a3b8" stroke-width="6"/>

        <rect x="285" y="12" width="420" height="160" rx="10" fill="none" stroke="#f97316" stroke-dasharray="6,4" stroke-width="2"/>
        <text x="495" y="31" fill="#f97316" font-size="12" font-weight="bold" text-anchor="middle">SSSF THRUSTER</text>

        {reg_svg}
        <line x1="405" y1="93" x2="435" y2="93" stroke="#94a3b8" stroke-width="6"/>
        {heater_svg}
        <line x1="540" y1="93" x2="570" y2="93" stroke="#94a3b8" stroke-width="6"/>

        <polygon points="570,73 595,84 655,58 655,128 595,102 570,113" fill="#334155" stroke="#e2e8f0" stroke-width="2"/>
        <text x="615" y="150" fill="#cbd5e1" font-size="11" text-anchor="middle">F = {F_curr_N:.2f} N</text>

        <polygon points="657,62 705,42 705,144 657,124" fill="#f97316" opacity="{plume_opacity}"/>
      </svg>
    </div>
    """