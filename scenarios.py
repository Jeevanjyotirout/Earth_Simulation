"""
Scenario Analysis Module for Earth System Simulation Engine.

Provides:
  • Pre-built named scenarios (BAU, Net-Zero, Green Utopia, etc.)
  • Sensitivity sweeps (vary one variable, observe outputs)
  • Multi-scenario comparison tables
"""

import numpy as np
from dataclasses import asdict
from climate_engine import (
    EarthSystemSimulationEngine,
    HumanDrivers,
    NaturalDrivers,
    AtmosphericState,
    SimulationOutputs,
)


# ─────────────────────────────────────────────────────────────────
# PRE-BUILT SCENARIOS
# ─────────────────────────────────────────────────────────────────

SCENARIOS = {
    "Pre-Industrial (1850)": dict(
        human=HumanDrivers(
            fossil_fuel_use=2, deforestation_rate=10, industrial_emissions=3,
            transport_emissions=2, agriculture_methane=15, urbanization=5,
            renewable_adoption=0, carbon_capture=0,
        ),
        atmosphere=AtmosphericState(co2_ppm=280, ch4_ppb=722, aerosols=0.05),
    ),
    "Business As Usual (2100)": dict(
        human=HumanDrivers(
            fossil_fuel_use=90, deforestation_rate=80, industrial_emissions=85,
            transport_emissions=80, agriculture_methane=75, urbanization=90,
            renewable_adoption=15, carbon_capture=5,
        ),
        atmosphere=AtmosphericState(co2_ppm=850, ch4_ppb=4500, aerosols=0.15),
    ),
    "Current Trajectory (2024)": dict(
        human=HumanDrivers(
            fossil_fuel_use=75, deforestation_rate=55, industrial_emissions=65,
            transport_emissions=65, agriculture_methane=50, urbanization=70,
            renewable_adoption=30, carbon_capture=8,
        ),
        atmosphere=AtmosphericState(co2_ppm=421, ch4_ppb=1900, aerosols=0.12),
    ),
    "Paris Agreement (2°C Path)": dict(
        human=HumanDrivers(
            fossil_fuel_use=40, deforestation_rate=25, industrial_emissions=35,
            transport_emissions=35, agriculture_methane=30, urbanization=55,
            renewable_adoption=65, carbon_capture=30,
        ),
        atmosphere=AtmosphericState(co2_ppm=480, ch4_ppb=2200, aerosols=0.10),
    ),
    "Net-Zero 2050": dict(
        human=HumanDrivers(
            fossil_fuel_use=15, deforestation_rate=10, industrial_emissions=15,
            transport_emissions=12, agriculture_methane=20, urbanization=60,
            renewable_adoption=85, carbon_capture=60,
        ),
        atmosphere=AtmosphericState(co2_ppm=430, ch4_ppb=1950, aerosols=0.09),
    ),
    "Green Utopia (2100)": dict(
        human=HumanDrivers(
            fossil_fuel_use=2, deforestation_rate=5, industrial_emissions=5,
            transport_emissions=3, agriculture_methane=10, urbanization=45,
            renewable_adoption=98, carbon_capture=90,
        ),
        atmosphere=AtmosphericState(co2_ppm=340, ch4_ppb=1600, aerosols=0.07),
    ),
    "Volcanic Super-Eruption": dict(
        human=HumanDrivers(
            fossil_fuel_use=50, deforestation_rate=40, industrial_emissions=45,
            transport_emissions=50, agriculture_methane=35, urbanization=60,
            renewable_adoption=25, carbon_capture=10,
        ),
        natural=NaturalDrivers(
            solar_radiation_change=-2.0, volcanic_activity=100,
            ocean_heat_uptake=50, ice_cover=55, surface_albedo=35,
        ),
        atmosphere=AtmosphericState(co2_ppm=421, ch4_ppb=1900, aerosols=1.0),
    ),
    "Solar Maximum + High CO₂": dict(
        human=HumanDrivers(
            fossil_fuel_use=80, deforestation_rate=60, industrial_emissions=70,
            transport_emissions=70, agriculture_methane=55, urbanization=75,
            renewable_adoption=20, carbon_capture=5,
        ),
        natural=NaturalDrivers(
            solar_radiation_change=2.5, volcanic_activity=0,
            ocean_heat_uptake=45, ice_cover=30, surface_albedo=25,
        ),
        atmosphere=AtmosphericState(co2_ppm=700, ch4_ppb=3500, aerosols=0.08),
    ),
}


def run_scenario(name: str) -> SimulationOutputs:
    """Run a named scenario and return outputs."""
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'. Choose from: {list(SCENARIOS)}")
    cfg = SCENARIOS[name]
    engine = EarthSystemSimulationEngine(
        human      = cfg.get("human",      HumanDrivers()),
        natural    = cfg.get("natural",    NaturalDrivers()),
        atmosphere = cfg.get("atmosphere", AtmosphericState()),
    )
    return engine.run()


def compare_all_scenarios(verbose=True) -> dict:
    """Run all scenarios and return a comparison dict."""
    results = {}
    for name in SCENARIOS:
        out = run_scenario(name)
        results[name] = out
        if verbose:
            print(f"\n{'━'*60}")
            print(f"  SCENARIO: {name}")
            print(out.summary())
    return results


# ─────────────────────────────────────────────────────────────────
# SENSITIVITY SWEEP
# ─────────────────────────────────────────────────────────────────

def sensitivity_sweep(
    driver_name: str,
    sweep_range=(0, 100),
    n_points: int = 25,
    fixed_human: HumanDrivers = None,
) -> dict:
    """
    Vary one human driver across a range while holding others fixed.
    Returns dict of sweep values and corresponding output arrays.

    Parameters
    ----------
    driver_name : str  — e.g. "fossil_fuel_use"
    sweep_range : tuple — (min, max)
    n_points    : int  — resolution
    fixed_human : HumanDrivers — baseline (default: current trajectory values)

    Returns
    -------
    dict with keys: driver_values, global_temp, jet_instability,
                    storm_risk, circulation_stability, rf
    """
    base = fixed_human or HumanDrivers(
        fossil_fuel_use=50, deforestation_rate=40, industrial_emissions=45,
        transport_emissions=50, agriculture_methane=35, urbanization=60,
        renewable_adoption=25, carbon_capture=10,
    )

    valid_drivers = list(base.__dataclass_fields__.keys())
    if driver_name not in valid_drivers:
        raise ValueError(f"'{driver_name}' not a valid driver. Choose from {valid_drivers}")

    driver_values      = np.linspace(*sweep_range, n_points)
    global_temp        = []
    jet_instability    = []
    storm_risk         = []
    circ_stability     = []
    rf_vals            = []

    for val in driver_values:
        h_copy = HumanDrivers(**{k: getattr(base, k) for k in valid_drivers})
        setattr(h_copy, driver_name, float(val))
        engine = EarthSystemSimulationEngine(human=h_copy)
        out = engine.run()
        global_temp.append(out.global_temp_change_c)
        jet_instability.append(out.jet_stream_instability)
        storm_risk.append(out.storm_risk_index)
        circ_stability.append(out.circulation_stability_score)
        rf_vals.append(out.radiative_forcing_wm2)

    return {
        "driver_name"          : driver_name,
        "driver_values"        : driver_values,
        "global_temp_c"        : np.array(global_temp),
        "jet_instability"      : np.array(jet_instability),
        "storm_risk"           : np.array(storm_risk),
        "circulation_stability": np.array(circ_stability),
        "radiative_forcing_wm2": np.array(rf_vals),
    }


def plot_sensitivity(sweep_result: dict, save_path: str = None):
    """Plot the results of a sensitivity_sweep call."""
    import matplotlib.pyplot as plt
    from visualizer import BG, PANEL_BG, TEXT, ACCENT, DANGER

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), facecolor=BG)
    fig.suptitle(
        f"Sensitivity Sweep: {sweep_result['driver_name'].replace('_', ' ').title()}",
        color=TEXT, fontsize=13, fontweight="bold",
    )

    x = sweep_result["driver_values"]
    pairs = [
        (axes[0, 0], sweep_result["global_temp_c"],         "Global Temp Change (°C)",       DANGER),
        (axes[0, 1], sweep_result["jet_instability"],        "Jet Stream Instability (0-10)", ACCENT),
        (axes[1, 0], sweep_result["storm_risk"],             "Storm Risk Index (0-10)",       "#f0a500"),
        (axes[1, 1], sweep_result["circulation_stability"],  "Circulation Stability (0-10)",  "#3fb950"),
    ]

    for ax, y, ylabel, color in pairs:
        ax.set_facecolor(PANEL_BG)
        for sp in ax.spines.values():
            sp.set_edgecolor("#30363d")
        ax.plot(x, y, color=color, linewidth=2)
        ax.fill_between(x, y, alpha=0.12, color=color)
        ax.set_xlabel(sweep_result["driver_name"].replace("_", " ").title(),
                      color=TEXT, fontsize=8)
        ax.set_ylabel(ylabel, color=TEXT, fontsize=8)
        ax.tick_params(colors=TEXT, labelsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight", facecolor=BG)
        plt.close(fig)
        print(f"  ✓ Sensitivity plot saved → {save_path}")
    else:
        plt.show()
    return fig
