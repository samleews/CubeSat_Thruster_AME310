from dataclasses import dataclass

@dataclass(frozen=True)
class IdealGas:
    name: str
    formula: str
    R: float          # Specific gas constant [J/(kg*K)]
    cp: float         # Constant-pressure specific heat [J/(kg*K)]
    molar_mass: float # [kg/kmol]

    @property
    def cv(self) -> float:
        return self.cp - self.R

    @property
    def gamma(self) -> float:
        return self.cp / self.cv

PROPELLANTS = {
    "Nitrogen (N2)": IdealGas(
        name="Nitrogen", formula="N2", R=296.8, cp=1039.0, molar_mass=28.013
    ),
    "Helium (He)": IdealGas(
        name="Helium", formula="He", R=2077.1, cp=5192.6, molar_mass=4.0026
    ),
    "Argon (Ar)": IdealGas(
        name="Argon", formula="Ar", R=208.1, cp=520.3, molar_mass=39.948
    ),
}

def get_propellant(key: str) -> IdealGas:
    if key not in PROPELLANTS:
        raise ValueError(f"Unknown propellant '{key}'. Choose from: {list(PROPELLANTS.keys())}")
    return PROPELLANTS[key]