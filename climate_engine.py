"""
╔══════════════════════════════════════════════════════════════════╗
║       EARTH SYSTEM SIMULATION ENGINE v1.0                       ║
║       Global Air Circulation & Climate Model                    ║
║       Author: Earth System Sim Engine                           ║
╚══════════════════════════════════════════════════════════════════╝

Based on simplified fluid dynamics, thermodynamics, and
atmospheric circulation physics. Suitable for educational and
research-grade scenario modeling.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Tuple
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────────────────────────

@dataclass
class HumanDrivers:
    """Human-induced climate forcing inputs (scale 0–100)."""
    fossil_fuel_use: float = 50.0
    deforestation_rate: float = 40.0
    industrial_emissions: float = 45.0
    transport_emissions: float = 50.0
    agriculture_methane: float = 35.0
    urbanization: float = 60.0
    renewable_adoption: float = 25.0
    carbon_capture: float = 10.0

    def validate(self):
        for fname, val in self.__dict__.items():
            if not (0 <= val <= 100):
                raise ValueError(f"{fname} must be between 0 and 100, got {val}")


@dataclass
class NaturalDrivers:
    """Natural climate forcing inputs."""
    solar_radiation_change: float = 0.0      # W/m² delta from baseline (~1361 W/m²)
    volcanic_activity: float = 0.0           # 0 = none, 100 = Pinatubo-scale
    ocean_heat_uptake: float = 50.0          # 0 = low, 100 = high
    ice_cover: float = 50.0                  # 0 = none, 100 = maximum
    surface_albedo: float = 30.0             # % reflectivity


@dataclass
class AtmosphericState:
    """Current atmospheric composition."""
    co2_ppm: float = 421.0                   # parts per million
    ch4_ppb: float = 1900.0                  # parts per billion
    aerosols: float = 0.1                    # AOD (Aerosol Optical Depth)


@dataclass
class CirculationCell:
    """Represents a single Hadley / Ferrel / Polar circulation cell."""
    name: str
    baseline_strength: float                 # relative units
    strength: float = field(init=False)
    latitudinal_shift_deg: float = 0.0
    disruption_index: float = 0.0            # 0=stable, 1=fully disrupted

    def __post_init__(self):
        self.strength = self.baseline_strength


@dataclass
class SimulationOutputs:
    """All diagnostic output fields."""
    # Temperature
    global_temp_change_c: float = 0.0
    arctic_amplification_c: float = 0.0
    tropical_temp_change_c: float = 0.0

    # Circulation metrics
    hadley_cell_expansion_deg: float = 0.0
    jet_stream_instability: float = 0.0       # 0–10
    itcz_shift_deg: float = 0.0               # degrees latitude
    trade_wind_change_pct: float = 0.0

    # Weather risk
    storm_risk_index: float = 0.0             # 0–10
    monsoon_strength_change_pct: float = 0.0
    drought_risk_index: float = 0.0           # 0–10
    flood_risk_index: float = 0.0             # 0–10

    # Stability
    circulation_stability_score: float = 10.0 # 10=perfectly stable, 0=chaotic
    polar_amplification_factor: float = 1.0

    # Derived atmospheric
    effective_co2_ppm: float = 421.0
    radiative_forcing_wm2: float = 0.0

    def summary(self) -> str:
        lines = [
            "═" * 60,
            "  EARTH SYSTEM SIMULATION — OUTPUT REPORT",
            "═" * 60,
            f"  🌡  Global Temp Change         : {self.global_temp_change_c:+.2f} °C",
            f"  🧊  Polar Amplification        : {self.polar_amplification_factor:.2f}×  ({self.arctic_amplification_c:+.2f} °C at poles)",
            f"  🌀  Hadley Cell Expansion       : {self.hadley_cell_expansion_deg:+.2f}°",
            f"  💨  Jet Stream Instability      : {self.jet_stream_instability:.1f} / 10",
            f"  🌐  ITCZ Shift                  : {self.itcz_shift_deg:+.2f}° lat",
            f"  🌬  Trade Wind Change           : {self.trade_wind_change_pct:+.1f}%",
            f"  ⛈   Storm Risk Index            : {self.storm_risk_index:.1f} / 10",
            f"  🌧  Monsoon Strength Change     : {self.monsoon_strength_change_pct:+.1f}%",
            f"  🔥  Drought Risk                : {self.drought_risk_index:.1f} / 10",
            f"  🌊  Flood Risk                  : {self.flood_risk_index:.1f} / 10",
            f"  🔄  Circulation Stability Score : {self.circulation_stability_score:.1f} / 10",
            f"  📡  Radiative Forcing           : {self.radiative_forcing_wm2:+.2f} W/m²",
            f"  🏭  Effective CO₂               : {self.effective_co2_ppm:.1f} ppm",
            "═" * 60,
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# CORE SIMULATION ENGINE
# ─────────────────────────────────────────────────────────────────

class EarthSystemSimulationEngine:
    """
    Simplified but physically-grounded Earth System Model.

    Physics basis:
    ─────────────
    • Radiative forcing from greenhouse gases follows IPCC AR6 relationships
    • Climate sensitivity: ECS ≈ 3.0 °C per CO₂ doubling (IPCC best estimate)
    • Polar amplification: ~2.5–3× global mean (Arctic Amplification)
    • Hadley Cell expansion: ~0.3–1.0° per °C global warming
    • Jet stream instability tied to equator-to-pole temperature gradient reduction
    """

    # Physical constants
    CLIMATE_SENSITIVITY = 3.0          # °C per CO₂ doubling (ECS)
    CO2_BASELINE = 280.0               # pre-industrial ppm
    STEFAN_BOLTZMANN = 5.67e-8         # W m⁻² K⁻⁴
    EARTH_ALBEDO_BASE = 0.30
    SOLAR_CONSTANT = 1361.0            # W/m²

    def __init__(
        self,
        human: HumanDrivers = None,
        natural: NaturalDrivers = None,
        atmosphere: AtmosphericState = None,
    ):
        self.human = human or HumanDrivers()
        self.natural = natural or NaturalDrivers()
        self.atmosphere = atmosphere or AtmosphericState()

        # Initialise circulation cells
        self.cells = {
            "hadley": CirculationCell("Hadley", baseline_strength=100.0),
            "ferrel": CirculationCell("Ferrel", baseline_strength=60.0),
            "polar":  CirculationCell("Polar",  baseline_strength=40.0),
        }

    # ──────────────────────────────────────────────────────────────
    # STEP 1 — Effective greenhouse gas concentrations
    # ──────────────────────────────────────────────────────────────
    def _compute_effective_ghg(self) -> Tuple[float, float]:
        """
        Translate human drivers into delta CO₂ and CH₄ concentrations.
        Each driver contributes a fractional increase above current levels.
        Returns (effective_co2_ppm, effective_ch4_ppb)
        """
        h = self.human

        # Net human emission scalar (0–1 range)
        emission_factor = (
            h.fossil_fuel_use * 0.30 +
            h.deforestation_rate * 0.15 +
            h.industrial_emissions * 0.20 +
            h.transport_emissions * 0.15 +
            h.agriculture_methane * 0.10 +
            h.urbanization * 0.05
        ) / 100.0  # max = 95 → normalise to ~1

        mitigation_factor = (
            h.renewable_adoption * 0.60 +
            h.carbon_capture * 0.40
        ) / 100.0

        net_emission = np.clip(emission_factor - mitigation_factor * 0.5, 0, 1)

        # CO₂ delta: up to +800 ppm above baseline at full emissions
        delta_co2 = net_emission * 800.0
        effective_co2 = self.atmosphere.co2_ppm + delta_co2

        # CH₄ delta driven mostly by agriculture and fossil fuels
        ch4_factor = (h.agriculture_methane * 0.50 + h.fossil_fuel_use * 0.30 +
                      h.deforestation_rate * 0.20) / 100.0
        delta_ch4 = ch4_factor * 3000.0
        effective_ch4 = self.atmosphere.ch4_ppb + delta_ch4

        return effective_co2, effective_ch4

    # ──────────────────────────────────────────────────────────────
    # STEP 2 — Radiative Forcing
    # ──────────────────────────────────────────────────────────────
    def _compute_radiative_forcing(self, eff_co2: float, eff_ch4: float) -> float:
        """
        IPCC AR5 simplified radiative forcing equations.

        CO₂:  RF = 5.35 × ln(C / C₀)                   [W/m²]
        CH₄:  RF = 0.036 × (√M − √M₀) − overlap terms  [W/m²]
        Solar: RF = ΔS / 4 × (1 − α)
        Volcano: negative RF via stratospheric aerosols
        """
        # CO₂ forcing
        rf_co2 = 5.35 * np.log(eff_co2 / self.CO2_BASELINE)

        # CH₄ forcing (simplified; ignoring N₂O overlap)
        ch4_0 = 722.0  # pre-industrial ppb
        rf_ch4 = 0.036 * (np.sqrt(eff_ch4) - np.sqrt(ch4_0))

        # Aerosol direct forcing (negative – cooling)
        rf_aerosol = -1.5 * self.atmosphere.aerosols

        # Solar forcing
        rf_solar = (self.natural.solar_radiation_change / 4.0) * (1.0 - self.EARTH_ALBEDO_BASE)

        # Volcanic forcing (eruption produces sulphate aerosols → cooling)
        # Pinatubo caused ~−3 W/m² for ~2 years
        rf_volcanic = -0.03 * self.natural.volcanic_activity

        # Albedo change from ice cover, deforestation, urbanisation
        delta_albedo = (
            (self.natural.ice_cover - 50) * 0.001 +           # more ice → higher albedo
            -(self.human.deforestation_rate - 50) * 0.0005 +  # less trees → higher albedo
            -(self.human.urbanization - 50) * 0.0003           # urban → lower albedo
        )
        rf_albedo = -(delta_albedo / 4.0) * self.SOLAR_CONSTANT

        total_rf = rf_co2 + rf_ch4 + rf_aerosol + rf_solar + rf_volcanic + rf_albedo
        return total_rf

    # ──────────────────────────────────────────────────────────────
    # STEP 3 — Temperature Response
    # ──────────────────────────────────────────────────────────────
    def _compute_temperature_change(self, rf: float) -> Dict[str, float]:
        """
        Global mean temperature change via climate sensitivity parameter λ.
        λ = ECS / (5.35 × ln2) ≈ 0.81 °C/(W/m²)
        Arctic amplification factor ≈ 2.5–3.0× global mean.
        """
        lambda_param = self.CLIMATE_SENSITIVITY / (5.35 * np.log(2.0))
        delta_t_global = lambda_param * rf

        # Ocean heat uptake delays and damps warming
        ocean_damping = 1.0 - (self.natural.ocean_heat_uptake / 100.0) * 0.30
        delta_t_global *= ocean_damping

        # Polar amplification (increases with warming)
        polar_amp = 2.5 + np.clip(delta_t_global * 0.15, 0, 1.0)
        delta_t_arctic = delta_t_global * polar_amp

        # Tropical (muted relative to global mean)
        delta_t_tropical = delta_t_global * 0.75

        return {
            "global": delta_t_global,
            "arctic": delta_t_arctic,
            "tropical": delta_t_tropical,
            "polar_amp_factor": polar_amp,
        }

    # ──────────────────────────────────────────────────────────────
    # STEP 4 — Atmospheric Circulation
    # ──────────────────────────────────────────────────────────────
    def _simulate_circulation(self, delta_t_global: float, delta_t_arctic: float) -> Dict:
        """
        Circulation changes driven by:
        • Reduced equator-to-pole temperature gradient → weaker jet, Hadley expansion
        • ITCZ shifts toward warmer hemisphere
        • Weakened trade winds under warming
        """
        h = self.human

        # ── Hadley Cell ───────────────────────────────────────────
        # Expands poleward ~0.5° per °C of global warming
        hadley_expansion = delta_t_global * 0.5
        # Additional expansion from surface warming asymmetry
        hadley_expansion += (h.fossil_fuel_use - h.renewable_adoption) / 100.0 * 1.5
        self.cells["hadley"].latitudinal_shift_deg = hadley_expansion

        # ── Equator-to-Pole Gradient ──────────────────────────────
        # Arctic warms faster → reduced gradient
        eq_pole_gradient_reduction = (delta_t_arctic - delta_t_global) / 30.0
        eq_pole_gradient_reduction = np.clip(eq_pole_gradient_reduction, 0, 1)

        # ── Jet Stream ───────────────────────────────────────────
        # Weakens and becomes more meandering as gradient reduces
        # Instability scale 0–10
        jet_instability = np.clip(
            eq_pole_gradient_reduction * 8.0 +
            delta_t_global * 0.4 +
            h.deforestation_rate / 100.0 * 1.5,
            0, 10
        )

        # ── ITCZ Shift ───────────────────────────────────────────
        # Shifts toward hemisphere receiving more energy / less aerosol loading
        # Simplified: NH warming bias from land → northward ITCZ shift
        itcz_shift = delta_t_global * 0.3 + (h.urbanization - 50) / 100.0 * 0.5

        # ── Trade Winds ──────────────────────────────────────────
        # Weaken with Hadley expansion and warming
        trade_wind_change_pct = -(hadley_expansion * 4.0 + delta_t_global * 1.5)
        trade_wind_change_pct = np.clip(trade_wind_change_pct, -40, 10)

        # ── Ferrel & Polar Cells ─────────────────────────────────
        ferrel_disruption = np.clip(eq_pole_gradient_reduction * 0.7, 0, 1)
        polar_disruption = np.clip(
            (delta_t_arctic / 10.0) * 0.8 +
            (1.0 - self.natural.ice_cover / 100.0) * 0.4,
            0, 1
        )
        self.cells["ferrel"].disruption_index = ferrel_disruption
        self.cells["polar"].disruption_index  = polar_disruption

        # ── Overall Circulation Stability ────────────────────────
        stability = 10.0 - (
            ferrel_disruption * 3.0 +
            polar_disruption  * 2.5 +
            jet_instability   * 0.3 +
            hadley_expansion  * 0.15
        )
        stability = np.clip(stability, 0, 10)

        return {
            "hadley_expansion": hadley_expansion,
            "jet_instability": jet_instability,
            "itcz_shift": itcz_shift,
            "trade_wind_change_pct": trade_wind_change_pct,
            "circulation_stability": stability,
        }

    # ──────────────────────────────────────────────────────────────
    # STEP 5 — Weather & Extreme Event Risk
    # ──────────────────────────────────────────────────────────────
    def _compute_weather_risk(
        self,
        delta_t: Dict,
        circulation: Dict,
    ) -> Dict:
        """
        Clausius-Clapeyron: +7% atmospheric moisture per °C warming →
        amplifies precipitation extremes, storm intensity.
        """
        dt_g = delta_t["global"]
        h = self.human

        # Moisture increase (Clausius-Clapeyron)
        moisture_increase = 0.07 * dt_g  # fractional

        # ── Storm Risk ───────────────────────────────────────────
        # Higher SSTs + moisture → stronger cyclones
        storm_risk = np.clip(
            dt_g * 1.2 +
            moisture_increase * 15.0 +
            circulation["jet_instability"] * 0.3 +
            (h.fossil_fuel_use / 100.0) * 1.5,
            0, 10
        )

        # ── Monsoon ──────────────────────────────────────────────
        # Intensifies with moisture but weakens if circulation disrupted
        monsoon_change_pct = (
            moisture_increase * 100.0 * 0.8 -
            circulation["hadley_expansion"] * 3.0 -
            h.deforestation_rate * 0.15
        )

        # ── Drought Risk ─────────────────────────────────────────
        # Subtropical drying + Hadley expansion pushes dry zones poleward
        drought_risk = np.clip(
            dt_g * 0.8 +
            circulation["hadley_expansion"] * 0.6 +
            h.deforestation_rate / 100.0 * 2.0 +
            (1 - self.natural.ocean_heat_uptake / 100.0) * 1.5,
            0, 10
        )

        # ── Flood Risk ───────────────────────────────────────────
        # More moisture, jet stream blocking → persistent rain events
        flood_risk = np.clip(
            moisture_increase * 20.0 +
            circulation["jet_instability"] * 0.5 +
            dt_g * 0.6,
            0, 10
        )

        return {
            "storm_risk": storm_risk,
            "monsoon_change_pct": monsoon_change_pct,
            "drought_risk": drought_risk,
            "flood_risk": flood_risk,
        }

    # ──────────────────────────────────────────────────────────────
    # PUBLIC — RUN FULL SIMULATION
    # ──────────────────────────────────────────────────────────────
    def run(self) -> SimulationOutputs:
        """Execute all simulation modules and return packaged outputs."""

        self.human.validate()

        # Pipeline
        eff_co2, eff_ch4 = self._compute_effective_ghg()
        rf = self._compute_radiative_forcing(eff_co2, eff_ch4)
        temp = self._compute_temperature_change(rf)
        circ = self._simulate_circulation(temp["global"], temp["arctic"])
        risk = self._compute_weather_risk(temp, circ)

        out = SimulationOutputs(
            global_temp_change_c       = round(temp["global"], 3),
            arctic_amplification_c     = round(temp["arctic"], 3),
            tropical_temp_change_c     = round(temp["tropical"], 3),
            hadley_cell_expansion_deg  = round(circ["hadley_expansion"], 2),
            jet_stream_instability     = round(circ["jet_instability"], 2),
            itcz_shift_deg             = round(circ["itcz_shift"], 2),
            trade_wind_change_pct      = round(circ["trade_wind_change_pct"], 2),
            storm_risk_index           = round(risk["storm_risk"], 2),
            monsoon_strength_change_pct= round(risk["monsoon_change_pct"], 2),
            drought_risk_index         = round(risk["drought_risk"], 2),
            flood_risk_index           = round(risk["flood_risk"], 2),
            circulation_stability_score= round(circ["circulation_stability"], 2),
            polar_amplification_factor = round(temp["polar_amp_factor"], 2),
            effective_co2_ppm          = round(eff_co2, 1),
            radiative_forcing_wm2      = round(rf, 3),
        )
        return out
