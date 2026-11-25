import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_transient_dashboard(res: dict) -> go.Figure:
    """4-panel time-series plot with shaded Burn 1, Coast, and Burn 2 regions."""
    t_min = res["t"] / 60.0
    t1 = res["t_burn1_end"] / 60.0
    t2 = res["t_coast_end"] / 60.0
    t3 = res["t_burn2_end"] / 60.0

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Tank Pressure P(t) [MPa]",
            "Tank Temperature T(t) [K]",
            "Propellant Mass m(t) [kg]",
            "Thruster Force F(t) [N]",
        ),
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )

    fig.add_trace(go.Scatter(x=t_min, y=res["P"] / 1e6, name="Pressure", line=dict(color="#38bdf8", width=2.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=t_min, y=res["T"], name="Temperature", line=dict(color="#f97316", width=2.5)), row=1, col=2)
    fig.add_trace(go.Scatter(x=t_min, y=res["m"], name="Mass", line=dict(color="#4ade80", width=2.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=t_min, y=res["F"], name="Thrust", line=dict(color="#e879f9", width=2.5)), row=2, col=2)

    # Valve freeze limit reference line on Temperature plot
    fig.add_hline(y=230.0, line_dash="dash", line_color="#ef4444", annotation_text="Freeze Limit (230 K)", row=1, col=2)

    # Shade Burn 1, Coast, and Burn 2 across all subplots
    for r in (1, 2):
        for c in (1, 2):
            fig.add_vrect(x0=0, x1=t1, fillcolor="rgba(239, 68, 68, 0.14)", line_width=0, row=r, col=c)
            fig.add_vrect(x0=t1, x1=t2, fillcolor="rgba(56, 189, 248, 0.08)", line_width=0, row=r, col=c)
            fig.add_vrect(x0=t2, x1=t3, fillcolor="rgba(239, 68, 68, 0.14)", line_width=0, row=r, col=c)

    fig.update_xaxes(title_text="Mission Time [min]", row=2, col=1)
    fig.update_xaxes(title_text="Mission Time [min]", row=2, col=2)
    fig.update_layout(
        height=560,
        showlegend=False,
        template="plotly_dark",
        margin=dict(l=40, r=20, t=45, b=40),
        title_text="Transient Tank & SSSF Thruster Response (Red = Burn | Blue = Coast)",
    )
    return fig


def plot_energy_balance(cons: dict) -> go.Figure:
    """Bar chart comparing initial internal energy, wall heat input, enthalpy outflow, and final internal energy."""
    labels = ["Initial U₁", "+ Tank Heat Q_in", "- Enthalpy Out E_out", "Final U₂"]
    values = [cons["U_init_kJ"], cons["Q_in_kJ"], -cons["E_out_kJ"], cons["U_final_kJ"]]
    colors = ["#38bdf8", "#facc15", "#f97316", "#4ade80"]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            text=[f"{v:.1f} kJ" for v in values],
            textposition="auto",
        )
    )
    fig.update_layout(
        title="Control Volume First Law Energy Balance [kJ]",
        yaxis_title="Energy [kJ]",
        template="plotly_dark",
        height=320,
        margin=dict(l=40, r=20, t=45, b=40),
    )
    return fig

METRIC_CONFIG = {
    "Cumulative Δv [m/s]": ("dv", 1.0, "#4ade80"),
    "Tank Pressure P(t) [MPa]": ("P", 1e-6, "#38bdf8"),
    "Tank Temperature T(t) [K]": ("T", 1.0, "#f97316"),
    "Propellant Mass m(t) [kg]": ("m", 1.0, "#a78bfa"),
    "Thruster Force F(t) [N]": ("F", 1.0, "#e879f9"),
    "Specific Impulse Isp [s]": ("isp", 1.0, "#facc15"),
}

def plot_single_live_metric(res: dict, metric_label: str, idx: int) -> go.Figure:
    """Plot a single selectable metric up to frame `idx` with fixed axes for live playback."""
    key, scale, color = METRIC_CONFIG[metric_label]
    t_full = res["t"]
    y_full = res[key] * scale

    t_curr = t_full[: idx + 1]
    y_curr = y_full[: idx + 1]

    y_min = float(min(y_full.min(), 0.0))
    y_max = float(y_full.max()) * 1.12 if y_full.max() > 0 else 1.0

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t_curr, y=y_curr,
            mode="lines",
            line=dict(color=color, width=3),
            name=metric_label,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[t_curr[-1]], y=[y_curr[-1]],
            mode="markers",
            marker=dict(size=10, color="white", line=dict(width=2.5, color=color)),
            showlegend=False,
        )
    )

    if key == "T":
        fig.add_hline(y=230.0, line_dash="dash", line_color="#ef4444", annotation_text="Freeze Limit (230 K)")

    fig.update_layout(
        title=f"Live Telemetry — {metric_label}",
        xaxis_title="Burn Time [s]",
        yaxis_title=metric_label,
        xaxis=dict(range=[0, max(1.0, float(t_full[-1]))]),
        yaxis=dict(range=[y_min, y_max]),
        template="plotly_dark",
        height=390,
        showlegend=False,
        margin=dict(l=50, r=25, t=45, b=45),
    )
    return fig

def plot_comparison_overlay(case_a: dict, case_b: dict, metric_label: str) -> go.Figure:
    """Overlay two saved Free-Play runs on a single chart for direct comparison."""
    key, scale, _ = METRIC_CONFIG[metric_label]
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=case_a["res"]["t"],
            y=case_a["res"][key] * scale,
            mode="lines",
            name=f"Case A: {case_a['label']}",
            line=dict(color="#38bdf8", width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=case_b["res"]["t"],
            y=case_b["res"][key] * scale,
            mode="lines",
            name=f"Case B: {case_b['label']}",
            line=dict(color="#f97316", width=3, dash="dash"),
        )
    )

    if key == "T":
        fig.add_hline(y=230.0, line_dash="dot", line_color="#ef4444", annotation_text="Freeze Limit (230 K)")

    fig.update_layout(
        title=f"Case A vs. Case B — {metric_label}",
        xaxis_title="Burn Time [s]",
        yaxis_title=metric_label,
        template="plotly_dark",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=50, r=25, t=60, b=45),
    )
    return fig