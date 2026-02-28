# 🌍 Earth System Simulation Engine

A physically-grounded Python simulation of global atmospheric circulation, climate feedback mechanisms, and extreme weather risk — driven by human and natural forcing inputs.

---

## Features

| Module | Description |
|---|---|
| `climate_engine.py` | Core simulation: GHG forcing → temperature → circulation → risk |
| `visualizer.py` | Multi-panel matplotlib diagnostic dashboards |
| `scenarios.py` | Pre-built scenarios + sensitivity sweep analysis |
| `main.py` | CLI entry point and interactive builder |
| `tests.py` | Physics-consistency unit tests (pytest) |

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/earth-climate-sim.git
cd earth-climate-sim
pip install -r requirements.txt

# Run full demo (all scenarios + dashboard PNG)
python main.py

# Run a specific scenario
python main.py --scenario "Net-Zero 2050" --dashboard

# Compare all scenarios
python main.py --compare-all

# Sensitivity sweep: how does storm risk change with fossil fuel use?
python main.py --sweep fossil_fuel_use

# Interactive custom scenario builder
python main.py --custom

# Run tests
python -m pytest tests.py -v
```

---

## Input Variables

### Human Drivers (0–100 scale)
| Variable | Description |
|---|---|
| `fossil_fuel_use` | Coal, oil, gas combustion intensity |
| `deforestation_rate` | Forest cover loss rate |
| `industrial_emissions` | Manufacturing and industrial CO₂/pollutants |
| `transport_emissions` | Road, air, shipping emissions |
| `agriculture_methane` | Livestock and paddy-field CH₄ |
| `urbanization` | Urban heat island expansion |
| `renewable_adoption` | Solar, wind, hydro deployment |
| `carbon_capture` | CCS and DAC deployment |

### Natural Drivers
| Variable | Range | Description |
|---|---|---|
| `solar_radiation_change` | W/m² delta | Change from 1361 W/m² baseline |
| `volcanic_activity` | 0–100 | Eruption scale (100 = Pinatubo) |
| `ocean_heat_uptake` | 0–100 | Rate of ocean heat absorption |
| `ice_cover` | 0–100 | Cryosphere extent |
| `surface_albedo` | % | Average surface reflectivity |

### Atmospheric State
| Variable | Unit | Pre-industrial |
|---|---|---|
| `co2_ppm` | ppm | 280 |
| `ch4_ppb` | ppb | 722 |
| `aerosols` | AOD | ~0.05 |

---

## Physics Basis

| Process | Equation / Reference |
|---|---|
| CO₂ radiative forcing | RF = 5.35 × ln(C/C₀) — IPCC AR5 |
| CH₄ radiative forcing | RF = 0.036 × (√M − √M₀) — IPCC AR5 |
| Climate sensitivity | ECS = 3.0 °C/doubling — IPCC AR6 best estimate |
| Arctic amplification | 2.5–3.0× global mean — observed + modelled |
| Hadley cell expansion | ~0.5°/°C warming — Held & Hou 1980, Lu et al. 2007 |
| Clausius-Clapeyron | +7% moisture/°C — underpins storm intensification |

---

## Sample Output

```
════════════════════════════════════════════════════════════
  EARTH SYSTEM SIMULATION — OUTPUT REPORT
════════════════════════════════════════════════════════════
  🌡  Global Temp Change         : +2.87 °C
  🧊  Polar Amplification        : 2.68×  (+7.69 °C at poles)
  🌀  Hadley Cell Expansion       : +3.11°
  💨  Jet Stream Instability      : 6.4 / 10
  🌐  ITCZ Shift                  : +1.21° lat
  🌬  Trade Wind Change           : -18.4%
  ⛈   Storm Risk Index            : 7.2 / 10
  🌧  Monsoon Strength Change     : +8.5%
  🔥  Drought Risk                : 6.9 / 10
  🌊  Flood Risk                  : 5.8 / 10
  🔄  Circulation Stability Score : 3.2 / 10
  📡  Radiative Forcing           : +6.83 W/m²
  🏭  Effective CO₂               : 1033.5 ppm
════════════════════════════════════════════════════════════
```

---

## Pre-built Scenarios

- Pre-Industrial (1850)
- Current Trajectory (2024)
- Business As Usual (2100)
- Paris Agreement (2°C Path)
- Net-Zero 2050
- Green Utopia (2100)
- Volcanic Super-Eruption
- Solar Maximum + High CO₂

---

## License

MIT License — free for educational, research, and personal use.

---

## Disclaimer

This is a **simplified educational model**, not a full General Circulation Model (GCM). It is designed to illustrate key physical relationships between climate drivers and atmospheric circulation, not to produce operational climate forecasts. For research-grade projections, consult CMIP6 models via [ESGF](https://esgf-node.llnl.gov/).
