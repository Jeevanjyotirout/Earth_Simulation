"""
Visualization module for Earth System Simulation Engine.
Generates professional multi-panel diagnostic plots.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable


# ─────────────────────────────────────────────────────────────────
# COLOUR PALETTES
# ─────────────────────────────────────────────────────────────────

TEMP_CMAP = LinearSegmentedColormap.from_list(
    "temp_diverge",
    ["#1a4fa0", "#4fc3f7", "#e0f7fa", "#fff8e1", "#ff7043", "#b71c1c"],
    N=256,
)

RISK_CMAP = LinearSegmentedColormap.from_list(
    "risk",
    ["#1b5e20", "#f9a825", "#b71c1c"],
    N=256,
)

BG = "#0d1117"
PANEL_BG = "#161b22"
TEXT = "#e6edf3"
ACCENT = "#58a6ff"
DANGER = "#f85149"
SAFE = "#3fb950"


# ─────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────

def plot_dashboard(outputs, human=None, title="Earth System Simulation — Diagnostic Dashboard"):
    """
    Render a 6-panel dashboard summarising all simulation outputs.
    Returns the matplotlib Figure object.
    """
    fig = plt.figure(figsize=(18, 12), facecolor=BG)
    fig.suptitle(title, fontsize=15, color=TEXT, fontweight="bold", y=0.98)

    gs = gridspec.GridSpec(
        3, 3,
        figure=fig,
        hspace=0.45,
        wspace=0.35,
        left=0.07, right=0.97,
        top=0.93, bottom=0.05,
    )

    axes = [fig.add_subplot(gs[r, c]) for r in range(3) for c in range(3)]
    for ax in axes:
        ax.set_facecolor(PANEL_BG)
        for spine in ax.spines.values():
            spine.set_edgecolor("#30363d")

    # ── Panel 0: Temperature Summary ────────────────────────────
    _panel_temp_bar(axes[0], outputs)

    # ── Panel 1: Circulation Stability Gauge ─────────────────────
    _panel_gauge(axes[1], outputs.circulation_stability_score,
                 "Circulation Stability", low_bad=True)

    # ── Panel 2: Jet Stream Instability Gauge ────────────────────
    _panel_gauge(axes[2], outputs.jet_stream_instability,
                 "Jet Stream Instability", low_bad=False)

    # ── Panel 3: Storm / Drought / Flood Risk Bars ───────────────
    _panel_risk_bars(axes[3], outputs)

    # ── Panel 4: Hadley / ITCZ / Trade Wind ──────────────────────
    _panel_circulation_metrics(axes[4], outputs)

    # ── Panel 5: Radiative Forcing Breakdown ─────────────────────
    _panel_rf(axes[5], outputs)

    # ── Panel 6: Scenario scan — temp vs CO₂ ────────────────────
    _panel_co2_temp_curve(axes[6], outputs)

    # ── Panel 7: Monsoon / Polar Amplification ───────────────────
    _panel_secondary_metrics(axes[7], outputs)

    # ── Panel 8: Human driver contribution ──────────────────────
    if human:
        _panel_human_drivers(axes[8], human)
    else:
        axes[8].axis("off")

    return fig


# ─────────────────────────────────────────────────────────────────
# INDIVIDUAL PANEL HELPERS
# ─────────────────────────────────────────────────────────────────

def _style_ax(ax, title):
    ax.set_title(title, color=ACCENT, fontsize=9, pad=6, fontweight="bold")
    ax.tick_params(colors=TEXT, labelsize=7)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)


def _panel_temp_bar(ax, out):
    labels = ["Global", "Tropical", "Arctic"]
    vals   = [out.global_temp_change_c, out.tropical_temp_change_c, out.arctic_amplification_c]
    colors = [DANGER if v > 0 else ACCENT for v in vals]

    bars = ax.barh(labels, vals, color=colors, height=0.5, edgecolor="#30363d")
    ax.axvline(0, color=TEXT, linewidth=0.8, alpha=0.4)
    for bar, v in zip(bars, vals):
        ax.text(v + (0.05 if v >= 0 else -0.05), bar.get_y() + bar.get_height() / 2,
                f"{v:+.2f}°C", va="center",
                ha="left" if v >= 0 else "right", color=TEXT, fontsize=8)
    ax.set_xlabel("°C change", color=TEXT, fontsize=7)
    _style_ax(ax, "Temperature Change")


def _panel_gauge(ax, value, label, low_bad=True, vmin=0, vmax=10):
    """Simple semicircular gauge."""
    theta = np.linspace(np.pi, 0, 300)
    r_in, r_out = 0.6, 1.0

    # Background arc segments (green → red)
    n_segs = 20
    seg_angles = np.linspace(np.pi, 0, n_segs + 1)
    for i in range(n_segs):
        frac = i / n_segs
        color = plt.cm.RdYlGn(1 - frac) if low_bad else plt.cm.RdYlGn(frac)
        ax.fill_between(
            [seg_angles[i+1], seg_angles[i]],
            r_in, r_out,
            transform=ax.transData,  # will patch below
        )

    ax.clear()
    ax.set_facecolor(PANEL_BG)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")

    for i in range(n_segs):
        frac = i / n_segs
        color = plt.cm.RdYlGn(1 - frac) if low_bad else plt.cm.RdYlGn(frac)
        a1, a2 = seg_angles[i+1], seg_angles[i]
        t = np.linspace(a1, a2, 30)
        x_out = np.cos(t) * r_out
        y_out = np.sin(t) * r_out
        x_in  = np.cos(t) * r_in
        y_in  = np.sin(t) * r_in
        xs = np.concatenate([x_out, x_in[::-1]])
        ys = np.concatenate([y_out, y_in[::-1]])
        ax.fill(xs, ys, color=color, alpha=0.85)

    # Needle
    frac_val = np.clip((value - vmin) / (vmax - vmin), 0, 1)
    needle_angle = np.pi * (1 - frac_val)
    nx = [0, 0.85 * np.cos(needle_angle)]
    ny = [0, 0.85 * np.sin(needle_angle)]
    ax.plot(nx, ny, color="white", linewidth=2.5, zorder=5)
    ax.plot(0, 0, "o", color="white", markersize=6, zorder=6)

    ax.text(0, -0.25, f"{value:.1f} / {int(vmax)}", ha="center",
            va="center", color=TEXT, fontsize=12, fontweight="bold")
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.4, 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(label, color=ACCENT, fontsize=9, pad=4, fontweight="bold")


def _panel_risk_bars(ax, out):
    risks = {
        "Storm Risk": out.storm_risk_index,
        "Drought Risk": out.drought_risk_index,
        "Flood Risk": out.flood_risk_index,
    }
    for i, (name, val) in enumerate(risks.items()):
        color = plt.cm.RdYlGn_r(val / 10)
        ax.barh(i, val, color=color, height=0.5, edgecolor="#30363d")
        ax.text(val + 0.1, i, f"{val:.1f}", va="center", color=TEXT, fontsize=8)

    ax.set_xlim(0, 11)
    ax.set_yticks(range(len(risks)))
    ax.set_yticklabels(list(risks.keys()), color=TEXT, fontsize=8)
    ax.set_xlabel("Risk Index (0–10)", color=TEXT, fontsize=7)
    ax.axvline(5, color="yellow", alpha=0.3, linewidth=1, linestyle="--")
    ax.axvline(8, color=DANGER, alpha=0.3, linewidth=1, linestyle="--")
    _style_ax(ax, "Extreme Weather Risk Indices")


def _panel_circulation_metrics(ax, out):
    metrics = {
        "Hadley Expansion (°)": out.hadley_cell_expansion_deg,
        "ITCZ Shift (°lat)": out.itcz_shift_deg,
        "Trade Wind Δ (%)": out.trade_wind_change_pct,
    }
    labels = list(metrics.keys())
    vals   = list(metrics.values())
    colors = [DANGER if v > 0 else ACCENT for v in vals]

    ax.barh(labels, vals, color=colors, height=0.5, edgecolor="#30363d")
    ax.axvline(0, color=TEXT, linewidth=0.8, alpha=0.4)
    for i, v in enumerate(vals):
        ax.text(v + (0.05 if v >= 0 else -0.05), i, f"{v:+.2f}",
                va="center", ha="left" if v >= 0 else "right",
                color=TEXT, fontsize=7)
    _style_ax(ax, "Circulation Metrics")


def _panel_rf(ax, out):
    """
    Approximate radiative forcing component breakdown from output.
    (We reconstruct rough estimates for visualisation.)
    """
    rf_total = out.radiative_forcing_wm2
    # Simple proportional split (indicative only)
    co2_frac  = 0.55
    ch4_frac  = 0.15
    aero_frac = -0.12
    solar_frac= 0.04
    other_frac= 1 - co2_frac - ch4_frac - aero_frac - solar_frac

    fracs  = [co2_frac, ch4_frac, aero_frac, solar_frac, other_frac]
    labels = ["CO₂", "CH₄", "Aerosols", "Solar", "Other"]
    colors = ["#e53935", "#fb8c00", "#90caf9", "#fdd835", "#80cbc4"]
    vals   = [rf_total * f for f in fracs]

    bars = ax.barh(labels, vals, color=colors, height=0.5, edgecolor="#30363d")
    ax.axvline(0, color=TEXT, linewidth=0.8, alpha=0.4)
    for bar, v in zip(bars, vals):
        ax.text(v + (0.02 if v >= 0 else -0.02), bar.get_y() + bar.get_height() / 2,
                f"{v:+.2f}", va="center",
                ha="left" if v >= 0 else "right", color=TEXT, fontsize=7)
    ax.set_xlabel("W/m²", color=TEXT, fontsize=7)
    _style_ax(ax, f"Radiative Forcing Breakdown  (Total: {rf_total:+.2f} W/m²)")


def _panel_co2_temp_curve(ax, out):
    """Equilibrium temperature vs CO₂ concentration curve."""
    co2_range = np.linspace(280, 1200, 300)
    lambda_p = 3.0 / (5.35 * np.log(2))
    delta_t = lambda_p * 5.35 * np.log(co2_range / 280.0)

    ax.plot(co2_range, delta_t, color=ACCENT, linewidth=1.8, label="ECS response")
    ax.axvline(out.effective_co2_ppm, color=DANGER, linestyle="--",
               linewidth=1.2, label=f"Sim CO₂: {out.effective_co2_ppm:.0f} ppm")
    ax.axhline(out.global_temp_change_c, color="#f0a500", linestyle=":",
               linewidth=1.2, label=f"ΔT: {out.global_temp_change_c:+.2f}°C")

    ax.scatter([out.effective_co2_ppm], [out.global_temp_change_c],
               color="white", s=60, zorder=5)

    ax.set_xlabel("Effective CO₂ (ppm)", fontsize=7)
    ax.set_ylabel("ΔT (°C)", fontsize=7)
    ax.legend(fontsize=6, facecolor=PANEL_BG, labelcolor=TEXT, edgecolor="#30363d")
    ax.axhspan(1.5, 2.0, alpha=0.15, color="yellow", label="Paris 1.5–2.0°C")
    ax.axhspan(2.0, delta_t.max(), alpha=0.08, color=DANGER)
    _style_ax(ax, "CO₂ → Temperature Sensitivity")


def _panel_secondary_metrics(ax, out):
    metrics = {
        "Monsoon Δ (%)": out.monsoon_strength_change_pct,
        "Polar Amp. (×)": (out.polar_amplification_factor - 1) * 10,
    }
    labels = list(metrics.keys())
    vals   = list(metrics.values())
    colors = [ACCENT if v > 0 else DANGER for v in vals]

    ax.bar(labels, vals, color=colors, edgecolor="#30363d", width=0.4)
    ax.axhline(0, color=TEXT, linewidth=0.8, alpha=0.4)
    for i, (l, v) in enumerate(zip(labels, vals)):
        ax.text(i, v + (0.3 if v >= 0 else -0.8), f"{v:+.2f}",
                ha="center", color=TEXT, fontsize=9)
    ax.set_ylabel("Scaled Value", color=TEXT, fontsize=7)
    _style_ax(ax, "Monsoon & Polar Amplification")


def _panel_human_drivers(ax, human):
    drivers = {
        "Fossil Fuel": human.fossil_fuel_use,
        "Deforestation": human.deforestation_rate,
        "Industry": human.industrial_emissions,
        "Transport": human.transport_emissions,
        "AgriMethane": human.agriculture_methane,
        "Urbanization": human.urbanization,
        "Renewables": human.renewable_adoption,
        "C-Capture": human.carbon_capture,
    }
    labels = list(drivers.keys())
    vals   = list(drivers.values())
    # Green for mitigation drivers, red for emission drivers
    colors = [SAFE if l in ("Renewables", "C-Capture") else DANGER for l in labels]

    bars = ax.barh(labels, vals, color=colors, height=0.55, edgecolor="#30363d")
    for bar, v in zip(bars, vals):
        ax.text(v + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{v:.0f}", va="center", color=TEXT, fontsize=7)
    ax.set_xlim(0, 110)
    ax.set_xlabel("Input Value (0–100)", color=TEXT, fontsize=7)
    _style_ax(ax, "Human Driver Inputs")


# ─────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────────────────────────

def save_dashboard(outputs, human=None, filepath="climate_dashboard.png", dpi=150):
    fig = plot_dashboard(outputs, human)
    fig.savefig(filepath, dpi=dpi, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  ✓ Dashboard saved → {filepath}")
    return filepath
