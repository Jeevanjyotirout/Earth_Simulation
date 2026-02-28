#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║   EARTH SYSTEM SIMULATION ENGINE — Command Line Interface           ║
║   Usage:  python main.py                                            ║
║           python main.py --scenario "Net-Zero 2050"                 ║
║           python main.py --compare-all                              ║
║           python main.py --sweep fossil_fuel_use                    ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import argparse
import sys
from climate_engine import (
    EarthSystemSimulationEngine,
    HumanDrivers,
    NaturalDrivers,
    AtmosphericState,
)
from scenarios import (
    SCENARIOS,
    run_scenario,
    compare_all_scenarios,
    sensitivity_sweep,
    plot_sensitivity,
)
from visualizer import save_dashboard


# ─────────────────────────────────────────────────────────────────
# INTERACTIVE DEMO (no args)
# ─────────────────────────────────────────────────────────────────

def interactive_demo():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║   🌍  EARTH SYSTEM SIMULATION ENGINE  v1.0                      ║
╚══════════════════════════════════════════════════════════════════╝
""")

    print("  Available scenarios:")
    for i, s in enumerate(SCENARIOS, 1):
        print(f"    [{i}]  {s}")

    print("\n  Running all scenarios...\n")
    results = compare_all_scenarios(verbose=True)

    # Save dashboard for the "Current Trajectory" scenario
    name = "Current Trajectory (2024)"
    out  = results[name]
    cfg  = SCENARIOS[name]
    save_dashboard(out, human=cfg.get("human"), filepath="climate_dashboard.png")

    # Sensitivity sweep example
    print("\n  Running sensitivity sweep: fossil_fuel_use → 0 to 100 ...\n")
    sweep = sensitivity_sweep("fossil_fuel_use")
    plot_sensitivity(sweep, save_path="sensitivity_fossil_fuel.png")

    print("""
  ✓ All done!
  Output files:
    • climate_dashboard.png
    • sensitivity_fossil_fuel.png
""")


# ─────────────────────────────────────────────────────────────────
# CUSTOM SCENARIO BUILDER
# ─────────────────────────────────────────────────────────────────

def build_custom_scenario():
    """Walk user through building a custom scenario interactively."""
    print("\n  ═══  CUSTOM SCENARIO BUILDER  ═══\n")
    print("  Enter human driver values (0–100). Press Enter to use defaults.\n")

    defaults = HumanDrivers()
    fields = {
        "fossil_fuel_use"    : ("Fossil Fuel Use",          defaults.fossil_fuel_use),
        "deforestation_rate" : ("Deforestation Rate",       defaults.deforestation_rate),
        "industrial_emissions": ("Industrial Emissions",    defaults.industrial_emissions),
        "transport_emissions": ("Transport Emissions",      defaults.transport_emissions),
        "agriculture_methane": ("Agriculture Methane",      defaults.agriculture_methane),
        "urbanization"       : ("Urbanization",             defaults.urbanization),
        "renewable_adoption" : ("Renewable Adoption",       defaults.renewable_adoption),
        "carbon_capture"     : ("Carbon Capture",           defaults.carbon_capture),
    }

    values = {}
    for key, (label, default) in fields.items():
        while True:
            try:
                raw = input(f"  {label:<26} [{default:.0f}]: ").strip()
                val = float(raw) if raw else default
                if not 0 <= val <= 100:
                    raise ValueError
                values[key] = val
                break
            except ValueError:
                print("    ⚠ Please enter a number between 0 and 100.")

    human = HumanDrivers(**values)
    engine = EarthSystemSimulationEngine(human=human)
    out = engine.run()
    print(out.summary())
    save = input("\n  Save dashboard PNG? [y/N]: ").strip().lower()
    if save == "y":
        save_dashboard(out, human=human, filepath="custom_scenario.png")


# ─────────────────────────────────────────────────────────────────
# CLI PARSER
# ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="Earth System Simulation Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--scenario", "-s", type=str, default=None,
        help=f"Run a named scenario. Choices: {list(SCENARIOS.keys())}",
    )
    parser.add_argument(
        "--compare-all", "-c", action="store_true",
        help="Run and print all pre-built scenarios.",
    )
    parser.add_argument(
        "--sweep", type=str, default=None,
        metavar="DRIVER",
        help="Run sensitivity sweep on a human driver variable.",
    )
    parser.add_argument(
        "--custom", action="store_true",
        help="Interactive custom scenario builder.",
    )
    parser.add_argument(
        "--dashboard", action="store_true",
        help="Save dashboard PNG for the chosen scenario.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.compare_all:
        compare_all_scenarios(verbose=True)
        return

    if args.sweep:
        sweep = sensitivity_sweep(args.sweep)
        plot_sensitivity(sweep, save_path=f"sensitivity_{args.sweep}.png")
        return

    if args.custom:
        build_custom_scenario()
        return

    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"  ✗ Unknown scenario '{args.scenario}'")
            print(f"  Available: {list(SCENARIOS.keys())}")
            sys.exit(1)
        out = run_scenario(args.scenario)
        print(out.summary())
        if args.dashboard:
            cfg = SCENARIOS[args.scenario]
            save_dashboard(out, human=cfg.get("human"),
                           filepath=f"dashboard_{args.scenario.replace(' ', '_')}.png")
        return

    # No args → full interactive demo
    interactive_demo()


if __name__ == "__main__":
    main()
