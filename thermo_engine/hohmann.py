import numpy as np

MU_EARTH = 3.986004418e14 # Earth gravitational parameter [m^3/s^2]
R_EARTH = 6371.0e3 # Mean Earth radius [m]

def compute_hohmann_targets(alt1_km: float, alt2_km: float) -> dict:
    """
    Calculate Hohmann transfer delta-v requirements and coast duration
    between two circular Earth orbits.
    """
    r1 = R_EARTH + alt1_km * 1000.0
    r2 = R_EARTH + alt2_km * 1000.0

    v_circ1 = np.sqrt(MU_EARTH / r1)
    v_circ2 = np.sqrt(MU_EARTH / r2)

    a_transfer = 0.5 * (r1 + r2)
    v_trans_p = np.sqrt(MU_EARTH * (2.0 / r1 - 1.0 / a_transfer))
    v_trans_a = np.sqrt(MU_EARTH * (2.0 / r2 - 1.0 / a_transfer))

    dv1 = abs(v_trans_p - v_circ1)
    dv2 = abs(v_circ2 - v_trans_a)
    t_coast = np.pi * np.sqrt(a_transfer**3 / MU_EARTH)

    return {
        "r1_m": r1,
        "r2_m": r2,
        "dv1_m_s": dv1,
        "dv2_m_s": dv2,
        "dv_total_m_s": dv1 + dv2,
        "t_coast_s": t_coast,
    }