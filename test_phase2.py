from thermo_engine.fluid_props import get_propellant
from thermo_engine.hohmann import compute_hohmann_targets
from thermo_engine.tank_transient import simulate_hohmann_mission

gas = get_propellant("Nitrogen (N2)")
targets = compute_hohmann_targets(alt1_km=400.0, alt2_km=450.0)

res = simulate_hohmann_mission(
    gas=gas,
    V_tank=0.004, # 4 L CubeSat tank
    P_init=20.0e6, # 20 MPa initial pressure
    T_init=295.0, # 295 K initial temperature
    m_dry=12.0, # 12 kg CubeSat
    A_throat=1.5e-6, # ~1.38 mm throat diameter
    area_ratio=50.0, # Vacuum nozzle expansion ratio
    dv1_target=targets["dv1_m_s"],
    dv2_target=targets["dv2_m_s"],
    t_coast=targets["t_coast_s"],
    Q_heater=25.0, # 25 W resistojet heater
    Q_tank_wall=2.0, # 2 W passive electronics heating
)

print(f"Target dv: {targets['dv_total_m_s']:.2f} m/s | Achieved dv: {res['dv'][-1]:.2f} m/s")
print(f"Burn 1: {res['t_burn1_end']:.1f} s | Coast: {targets['t_coast_s']/60:.1f} min | Burn 2: {res['t_burn2_end'] - res['t_coast_end']:.1f} s")
print(f"Propellant: {res['m_init']:.3f} kg -> {res['m'][-1]:.3f} kg")
print(f"Min Tank Temp: {res['T'].min():.1f} K | Final Tank Pressure: {res['P'][-1]/1e6:.2f} MPa")