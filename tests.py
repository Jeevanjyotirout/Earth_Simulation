"""
Unit tests for Earth System Simulation Engine.
Run with:  python -m pytest tests.py -v
"""

import pytest
import numpy as np
from climate_engine import (
    EarthSystemSimulationEngine,
    HumanDrivers,
    NaturalDrivers,
    AtmosphericState,
)
from scenarios import run_scenario, sensitivity_sweep


class TestInputValidation:
    def test_valid_inputs_pass(self):
        h = HumanDrivers(fossil_fuel_use=50, renewable_adoption=30)
        h.validate()  # should not raise

    def test_out_of_range_raises(self):
        h = HumanDrivers(fossil_fuel_use=150)
        with pytest.raises(ValueError):
            h.validate()

    def test_negative_raises(self):
        h = HumanDrivers(deforestation_rate=-5)
        with pytest.raises(ValueError):
            h.validate()


class TestPhysicalConsistency:
    """Verify that simulation outputs are physically plausible."""

    def _run_with(self, **kwargs):
        h = HumanDrivers(**kwargs)
        return EarthSystemSimulationEngine(human=h).run()

    def test_high_emissions_warm_more(self):
        out_high = self._run_with(fossil_fuel_use=90, renewable_adoption=5)
        out_low  = self._run_with(fossil_fuel_use=10, renewable_adoption=90)
        assert out_high.global_temp_change_c > out_low.global_temp_change_c, \
            "High emissions should produce more warming"

    def test_renewables_reduce_warming(self):
        out_no_ren  = self._run_with(fossil_fuel_use=80, renewable_adoption=0,  carbon_capture=0)
        out_max_ren = self._run_with(fossil_fuel_use=80, renewable_adoption=100, carbon_capture=80)
        assert out_max_ren.global_temp_change_c < out_no_ren.global_temp_change_c

    def test_polar_amplification_greater_than_global(self):
        out = self._run_with(fossil_fuel_use=70)
        assert out.arctic_amplification_c >= out.global_temp_change_c, \
            "Arctic must warm at least as much as global mean"

    def test_high_emissions_reduce_circulation_stability(self):
        out_high = self._run_with(fossil_fuel_use=95, deforestation_rate=90)
        out_low  = self._run_with(fossil_fuel_use=5,  deforestation_rate=5, renewable_adoption=95)
        assert out_high.circulation_stability_score < out_low.circulation_stability_score

    def test_output_ranges(self):
        out = self._run_with(fossil_fuel_use=60)
        assert 0 <= out.storm_risk_index <= 10
        assert 0 <= out.drought_risk_index <= 10
        assert 0 <= out.flood_risk_index <= 10
        assert 0 <= out.jet_stream_instability <= 10
        assert 0 <= out.circulation_stability_score <= 10

    def test_positive_radiative_forcing_warms(self):
        engine = EarthSystemSimulationEngine(
            atmosphere=AtmosphericState(co2_ppm=800, ch4_ppb=4000)
        )
        out = engine.run()
        assert out.radiative_forcing_wm2 > 0
        assert out.global_temp_change_c > 0

    def test_volcanic_eruption_cools(self):
        engine_no_volcano = EarthSystemSimulationEngine(
            natural=NaturalDrivers(volcanic_activity=0)
        )
        engine_volcano = EarthSystemSimulationEngine(
            natural=NaturalDrivers(volcanic_activity=100)
        )
        out_no_v = engine_no_volcano.run()
        out_v    = engine_volcano.run()
        assert out_v.global_temp_change_c < out_no_v.global_temp_change_c, \
            "Volcanic eruption should reduce temperature via sulphate cooling"

    def test_solar_increase_warms(self):
        engine_solar = EarthSystemSimulationEngine(
            natural=NaturalDrivers(solar_radiation_change=5.0)
        )
        engine_base  = EarthSystemSimulationEngine(
            natural=NaturalDrivers(solar_radiation_change=0.0)
        )
        assert engine_solar.run().global_temp_change_c > engine_base.run().global_temp_change_c


class TestScenarios:
    def test_all_scenarios_run(self):
        from scenarios import SCENARIOS
        for name in SCENARIOS:
            out = run_scenario(name)
            assert out.global_temp_change_c is not None

    def test_bau_warmer_than_net_zero(self):
        bau      = run_scenario("Business As Usual (2100)")
        net_zero = run_scenario("Net-Zero 2050")
        assert bau.global_temp_change_c > net_zero.global_temp_change_c

    def test_green_utopia_most_stable(self):
        utopia = run_scenario("Green Utopia (2100)")
        bau    = run_scenario("Business As Usual (2100)")
        assert utopia.circulation_stability_score > bau.circulation_stability_score


class TestSensitivitySweep:
    def test_sweep_returns_correct_shape(self):
        result = sensitivity_sweep("fossil_fuel_use", n_points=10)
        assert len(result["driver_values"]) == 10
        assert len(result["global_temp_c"])  == 10

    def test_sweep_is_monotonic_for_fossil_fuel(self):
        result = sensitivity_sweep("fossil_fuel_use", n_points=20)
        diffs = np.diff(result["global_temp_c"])
        # Temperature should be non-decreasing as fossil fuel use increases
        assert np.all(diffs >= -0.01), \
            "Global temp should increase (or stay flat) with increasing fossil fuel use"

    def test_invalid_driver_raises(self):
        with pytest.raises(ValueError):
            sensitivity_sweep("not_a_real_driver")
