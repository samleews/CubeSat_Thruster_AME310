from thermo_engine.fluid_props import get_propellant
from thermo_engine.hohmann import compute_hohmann_targets
from thermo_engine.tank_transient import simulate_hohmann_mission
from thermo_engine.validation import (
    audit_conservation,
    audit_second_law,
    benchmark_analytical_blowdown,
    check_solver_stability,
)

gas = get_propellant("Nitrogen (N2)")
targets = compute_hohmann_targets(alt1_km=400.0, alt2_km=450.0)

sim_kwargs = dict(
    gas=gas,
    V_tank=0.004,
    P_init=20.0e6,
    T_init=295.0,
    m_dry=12.0,
    A_throat=1.5e-6,
    area_ratio=50.0,
    dv1_target=targets["dv1_m_s"],
    dv2_target=targets["dv2_m_s"],
    t_coast=targets["t_coast_s"],
    eta_nozzle=0.92,
    Q_heater=25.0,
    Q_tank_wall=2.0,
)

res = simulate_hohmann_mission(**sim_kwargs)

cons = audit_conservation(res, gas)
sec = audit_second_law(res, gas, 1.5e-6, 50.0, 0.92, 25.0)
bench = benchmark_analytical_blowdown(gas, 0.004, 20.0e6, 295.0, 12.0, 1.5e-6, 50.0)
stab = check_solver_stability(sim_kwargs)

print("=== PHASE 3 VALIDATION REPORT ===")
print(f"1. Energy Conservation : {'PASS' if cons['passed'] else 'FAIL'} | Rel Error = {cons['energy_rel_err']:.2e} (Residual = {cons['energy_residual_J']:.4f} J)")
print(f"2. Second Law (Nozzle) : {'PASS' if sec['passed'] else 'FAIL'} | Min S_gen = {sec['min_S_gen_W_K']:.4f} W/K")
print(f"3. Analytical Blowdown : {'PASS' if bench['passed'] else 'FAIL'} | Max Temp Error = {bench['max_abs_err_K']:.2e} K ({bench['max_rel_err']:.2e})")
print(f"4. Solver Stability    : {'PASS' if stab['passed'] else 'FAIL'} | Baseline vs Fine Max Rel Diff = {max(stab['dv_rel_diff'], stab['m_rel_diff'], stab['T_rel_diff']):.2e}")