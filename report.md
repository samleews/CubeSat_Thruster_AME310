AME 310, Fall 2026
[Last Name, First Name]
November 23, 2026

## Abstract

An integrated thermodynamic model and interactive virtual laboratory were developed to simulate a CubeSat cold-gas and resistojet propulsion system executing continuous blowdown and two-burn Hohmann orbit-raising maneuvers. The propulsion architecture coupled a variable-mass, transient pressurized propellant tank with Steady-State Steady-Flow (SSSF) components, comprising an optional isenthalpic pressure regulator, an optional electrical resistojet heater, and a choked converging-diverging vacuum nozzle. The coupled ordinary differential equations were integrated using an adaptive Runge-Kutta solver with exact ideal-gas property identities enforced to machine precision. Numerical verification confirmed First Law energy conservation with a relative error of $3.58 \times 10^{-10}$ ($0.0001\text{ J}$ residual), Second Law compliance with a minimum nozzle entropy generation rate of $11.60\text{ W/K}$, analytical isentropic blowdown agreement within $1.26 \times 10^{-10}$ ($3.23 \times 10^{-8}\text{ K}$), and solver tolerance convergence within $1.25 \times 10^{-10}$. Five parametric investigations quantified system sensitivity to resistojet heater power ($0\text{--}100\text{ W}$), propellant molar mass ($\text{N}_2$, $\text{He}$, $\text{Ar}$), pressure regulation ($3\text{--}8\text{ MPa}$), nozzle throat diameter ($0.8\text{--}2.4\text{ mm}$), and coast-phase wall heating ($0\text{--}6\text{ W}$). Results demonstrated that while helium maximized peak specific impulse at $169.4\text{ s}$, nitrogen delivered the highest total velocity increment ($43.31\text{ m/s}$ versus $13.40\text{ m/s}$ for helium) in a volume-constrained $4.0\text{ L}$ tank owing to sevenfold greater stored mass ($0.9137\text{ kg}$ versus $0.1306\text{ kg}$). During a $400\text{ km}$ to $450\text{ km}$ Hohmann transfer ($\Delta v = 28.17\text{ m/s}$), $6.0\text{ W}$ of ambient tank wall heating during the coast phase was required to maintain tank temperatures above the $230\text{ K}$ valve-freezing limit, achieving a minimum temperature of $239.6\text{ K}$ with $43.4\%$ propellant remaining.

## 1. Introduction

Small-satellite orbital maneuvering relies on compact propulsion systems capable of delivering precise velocity increments ($\Delta v$) under strict volume, mass, and electrical power constraints. Cold-gas and resistojet thrusters are widely deployed on CubeSats because they utilize non-toxic, inert propellants stored in high-pressure tanks. Accurately predicting mission performance requires coupling the transient thermodynamics of the depleting propellant tank with the quasi-steady compressible flow of the downstream thruster assembly.

For the transient propellant tank control volume of fixed internal volume $V$ ($\text{m}^3$), conservation of mass relates the instantaneous propellant mass $m$ ($\text{kg}$) to the nozzle mass flow rate $\dot{m}$ ($\text{kg/s}$) as

$$\frac{dm}{dt} = -\dot{m}. \tag{1}$$

Applying the First Law of Thermodynamics to the uniform-state, uniform-flow tank control volume with ambient wall heat transfer rate $\dot{Q}_{\text{wall}}$ ($\text{W}$) and zero shaft work yields

$$\frac{dU}{dt} = \dot{Q}_{\text{wall}} - \dot{m} h_{\text{tank}}, \tag{2}$$

where $U = m c_v T$ is the total internal energy ($\text{J}$), $h_{\text{tank}} = c_p T$ is the specific enthalpy of the exiting gas ($\text{J/kg}$), $T$ is the tank gas temperature ($\text{K}$), and $c_v$ and $c_p$ are the constant-volume and constant-pressure specific heats ($\text{J/(kg}\cdot\text{K)}$), respectively. Expanding the left-hand side of Equation (2) by the product rule and substituting Equation (1) gives

$$m c_v \frac{dT}{dt} - \dot{m} c_v T = \dot{Q}_{\text{wall}} - \dot{m} c_p T. \tag{3}$$

Rearranging Equation (3) and applying the ideal-gas identities $c_p - c_v = R$ and $\gamma = c_p / c_v$ yields the transient tank temperature rate equation:

$$\frac{dT}{dt} = \frac{\dot{Q}_{\text{wall}}}{m c_v} - (\gamma - 1)\frac{T}{m}\dot{m}, \tag{4}$$

where $R$ is the specific gas constant ($\text{J/(kg}\cdot\text{K)}$) and $\gamma$ is the dimensionless specific heat ratio. Tank pressure $P$ ($\text{Pa}$) is governed at every instant by the ideal-gas equation of state,

$$P = \frac{m R T}{V}. \tag{5}$$

In the adiabatic limit ($\dot{Q}_{\text{wall}} = 0$), Equations (1), (4), and (5) admit an exact analytical isentropic blowdown benchmark:

$$\frac{T}{T_0} = \left(\frac{P}{P_0}\right)^{\frac{\gamma - 1}{\gamma}}, \tag{6}$$

where $P_0$ and $T_0$ denote the initial tank pressure and temperature.

Downstream of the tank, the internal volume of the feed lines, regulator, heater, and nozzle is negligible compared to $V$, allowing those devices to be modeled as Steady-State Steady-Flow (SSSF) control volumes. When the optional pressure regulator is enabled and $P > P_{\text{reg}}$, the valve throttles the propellant isenthalpically ($h_1 = h_2$, hence $T_2 = T_1$ for an ideal gas) to a constant chamber pressure $P_c = P_{\text{reg}}$; once $P \le P_{\text{reg}}$, the regulator drops out and $P_c = P$. Entropy generation across the throttling regulator is given by

$$\dot{S}_{\text{gen,reg}} = -\dot{m} R \ln\left(\frac{P_c}{P}\right) \ge 0. \tag{7}$$

When the optional resistojet heater is active, electrical heat input $\dot{Q}_{\text{heater}}$ ($\text{W}$) raises the stagnation temperature entering the nozzle according to the SSSF energy balance:

$$T_{0,\text{exit}} = T + \frac{\dot{Q}_{\text{heater}}}{\dot{m} c_p}. \tag{8}$$

Because the converging-diverging nozzle exhausts into a vacuum ($P_a = 0\text{ Pa}$), the throat of area $A^*$ ($\text{m}^2$) remains choked ($M^* = 1$) throughout every burn. The choked mass flow rate is

$$\dot{m} = \frac{P_c A^*}{\sqrt{T_{0,\text{exit}}}} \sqrt{\frac{\gamma}{R}} \left(\frac{2}{\gamma + 1}\right)^{\frac{\gamma + 1}{2(\gamma - 1)}}. \tag{9}$$

For a specified nozzle expansion ratio $A_e / A^*$, the supersonic exit Mach number $M_e > 1$ is determined from the isentropic area-Mach relation:

$$\frac{A_e}{A^*} = \frac{1}{M_e} \left[\frac{2}{\gamma + 1}\left(1 + \frac{\gamma - 1}{2} M_e^2\right)\right]^{\frac{\gamma + 1}{2(\gamma - 1)}}. \tag{10}$$

Incorporating nozzle isentropic efficiency $\eta_N$, the actual exhaust velocity $v_e$ ($\text{m/s}$), vacuum thrust $F$ ($\text{N}$), and specific impulse $I_{sp}$ ($\text{s}$) are evaluated as

$$v_e = \sqrt{2 \eta_N c_p T_{0,\text{exit}} \left[1 - \left(1 + \frac{\gamma - 1}{2} M_e^2\right)^{-1}\right]}, \tag{11}$$

$$F = \dot{m} v_e + P_e A_e, \qquad I_{sp} = \frac{F}{\dot{m} g_0}, \tag{12}$$

where $P_e$ is the nozzle exit static pressure ($\text{Pa}$) and $g_0 = 9.80665\text{ m/s}^2$ is standard gravity. Second Law compliance across the adiabatic nozzle expansion requires non-negative entropy generation:

$$\dot{S}_{\text{gen,nozzle}} = \dot{m} \left[c_p \ln\left(\frac{T_e}{T_{0,\text{exit}}}\right) - R \ln\left(\frac{P_e}{P_c}\right)\right] \ge 0. \tag{13}$$

Spacecraft velocity increment $\Delta v$ ($\text{m/s}$) is integrated over the finite burn duration for a spacecraft of dry mass $m_{\text{dry}}$ ($\text{kg}$) via

$$\frac{d(\Delta v)}{dt} = \frac{F}{m_{\text{dry}} + m(t)}. \tag{14}$$

For two-burn Hohmann orbit-raising maneuvers between circular orbits of radii $r_1$ and $r_2$, target velocity increments ($\Delta v_1$, $\Delta v_2$) and coast duration ($t_{\text{coast}}$) are computed from the vis-viva equations using Earth's gravitational parameter $\mu = 3.986 \times 10^{14}\text{ m}^3/\text{s}^2$.

## 2. Materials and Methods

The thermodynamic model was implemented in a modular Python architecture separating fluid properties, SSSF nozzle calculations, transient ordinary differential equation (ODE) integration, and validation auditing. Propellants ($\text{N}_2$, $\text{He}$, and $\text{Ar}$) were modeled as calorically perfect ideal gases with $c_v = c_p - R$ and $\gamma = c_p / c_v$ computed directly from $c_p$ and $R$ to eliminate rounding discrepancies in the energy balance. The supersonic exit Mach number in Equation (10) was solved numerically using Brent's root-finding method (`scipy.optimize.brentq`) to a tolerance of $10^{-12}$.

Time integration of Equations (1), (4), and (14), alongside cumulative energy outflow ($E_{\text{out}} = \int \dot{m} c_p T\,dt$) and wall heat input ($Q_{\text{in}} = \int \dot{Q}_{\text{wall}}\,dt$), was performed using an explicit adaptive Runge-Kutta solver (`scipy.integrate.solve_ivp`, RK45 method) with baseline relative and absolute tolerances of $10^{-7}$ and $10^{-9}$, respectively. Terminal event functions halted integration automatically upon reaching target $\Delta v$ values during Hohmann burns or upon reaching a minimum residual propellant fraction of $2\%$ ($m_{\text{min}} = 0.02 m_0$). During the Hohmann coast phase, $\dot{m}$ was set to zero while Equation (4) continued integrating transient wall heating.

Figure 1 illustrates the coupled control volume schematic deployed in the interactive Streamlit virtual laboratory. The interface was organized into four modes via a top navigation bar: Free-Play Mode (featuring a 60 FPS client-side HTML/SVG/Canvas playback engine, automatic x- and y-axis annotations for valve freezing below $230\text{ K}$ and tank depletion, 1-click presets, a Simple/Advanced control toggle, and a 5-step Guided Walkthrough), Mission Mode (three engineering-scored Hohmann transfer challenges), Comparison Mode (side-by-side Case A versus Case B overlays), and Validation Audit (real-time First and Second Law verification).

![System Schematic](report_figures/schematic_placeholder.png)

*Figure 1. Coupled control volume schematic distinguishing the transient pressurized propellant tank from the SSSF pressure regulator, resistojet heater, and vacuum converging-diverging nozzle. Optional SSSF devices are bypassed visually and mathematically when disabled.*

## 3. Results

### 3.1 Verification and Validation

Prior to parametric analysis, the numerical engine was audited across four independent benchmarks using a baseline $400\text{ km}$ to $450\text{ km}$ nitrogen Hohmann transfer ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $T_0 = 295\text{ K}$, $m_{\text{dry}} = 12.0\text{ kg}$, $d^* = 1.4\text{ mm}$, $A_e/A^* = 50$, $\eta_N = 0.92$, $\dot{Q}_{\text{heater}} = 25\text{ W}$, $\dot{Q}_{\text{wall}} = 2.0\text{ W}$). As summarized in Table 1, all four validation criteria passed by several orders of magnitude. Enforcing exact ideal-gas identities reduced the First Law energy residual between $\Delta U_{\text{tank}}$ and $Q_{\text{in}} - E_{\text{out}}$ to $0.0001\text{ J}$ ($3.58 \times 10^{-10}$ relative error), while solver tolerance sweeps confirmed numerical invariance within $1.25 \times 10^{-10}$ between baseline ($10^{-7}$) and fine ($10^{-9}$) tolerances.

*Table 1. Quantitative verification and validation audit results for the coupled transient-tank and SSSF-nozzle solver.*

| Validation Benchmark | Acceptance Criterion | Measured Result | Status |
| :--- | :--- | :--- | :--- |
| First Law Energy Conservation | Relative Error $< 10^{-5}$ | $3.58 \times 10^{-10}$ ($0.0001\text{ J}$) | PASS |
| Second Law (SSSF Nozzle) | $\min(\dot{S}_{\text{gen}}) \ge 0\text{ W/K}$ | $11.60\text{ W/K}$ | PASS |
| Analytical Isentropic Blowdown | Max Temp Rel. Error $< 10^{-5}$ | $1.26 \times 10^{-10}$ ($3.23 \times 10^{-8}\text{ K}$) | PASS |
| ODE Solver Tolerance Stability | Baseline vs. Fine Diff $< 10^{-4}$ | $1.25 \times 10^{-10}$ | PASS |

### 3.2 Parametric Investigations

Five parametric studies were conducted from the baseline configuration ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $T_0 = 295\text{ K}$, $m_{\text{dry}} = 12.0\text{ kg}$, $d^* = 1.4\text{ mm}$, $A_e/A^* = 50$, $\eta_N = 0.92$). Study 1 swept resistojet heater power from $0\text{ W}$ to $100\text{ W}$ over a $90\text{ s}$ adiabatic nitrogen blowdown. As shown in Table 2 and Figure 2, increasing heater power from $0\text{ W}$ to $100\text{ W}$ raised final $\Delta v$ from $43.31\text{ m/s}$ to $44.44\text{ m/s}$ ($+2.6\%$) and elevated peak $I_{sp}$ from $73.2\text{ s}$ to $80.5\text{ s}$ ($+10.0\%$), while slightly reducing propellant expenditure from $0.8954\text{ kg}$ to $0.8927\text{ kg}$.

*Table 2. Effect of resistojet heater power on 90 s adiabatic nitrogen blowdown performance ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $T_0 = 295\text{ K}$).*

| Heater Power [W] | Final $\Delta v$ [m/s] | Peak $I_{sp}$ [s] | Propellant Used [kg] | Min Tank Temp [K] |
| :--- | :--- | :--- | :--- | :--- |
| 0.0 | 43.31 | 73.2 | 0.8954 | 61.7 |
| 25.0 | 43.61 | 73.2 | 0.8954 | 61.7 |
| 50.0 | 43.94 | 73.2 | 0.8954 | 61.7 |
| 75.0 | 44.22 | 73.3 | 0.8945 | 63.0 |
| 100.0 | 44.44 | 80.5 | 0.8927 | 65.3 |

![Study 1](report_figures/study1_heater_sweep.png)

*Figure 2. Cumulative $\Delta v$ history for a 90 s nitrogen blowdown across resistojet heater powers from 0 W to 100 W ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $d^* = 1.4\text{ mm}$). Increasing electrical heat input monotonically elevates total $\Delta v$ by raising nozzle stagnation temperature.*

Study 2 compared nitrogen ($\text{N}_2$), helium ($\text{He}$), and argon ($\text{Ar}$) at identical initial storage conditions ($4.0\text{ L}$, $20.0\text{ MPa}$, $295\text{ K}$). As presented in Table 3 and Figure 3, helium achieved the highest peak specific impulse at $169.4\text{ s}$—more than double that of nitrogen ($73.2\text{ s}$) and triple that of argon ($53.6\text{ s}$)—but yielded the lowest total $\Delta v$ ($13.40\text{ m/s}$) due to its small initial stored mass ($0.1306\text{ kg}$). Nitrogen delivered the highest total $\Delta v$ at $43.31\text{ m/s}$, outperforming argon ($39.89\text{ m/s}$) despite storing $30\%$ less initial mass.

*Table 3. Propellant species performance comparison for a 90 s unheated blowdown ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $T_0 = 295\text{ K}$).*

| Propellant | Initial Mass [kg] | Final $\Delta v$ [m/s] | Peak $I_{sp}$ [s] | Min Tank Temp [K] |
| :--- | :--- | :--- | :--- | :--- |
| Helium ($\text{He}$) | 0.1306 | 13.40 | 169.4 | 21.7 |
| Nitrogen ($\text{N}_2$) | 0.9137 | 43.31 | 73.2 | 61.7 |
| Argon ($\text{Ar}$) | 1.3032 | 39.89 | 53.6 | 31.2 |

![Study 2](report_figures/study2_propellant_tradeoff.png)

*Figure 3. Specific impulse histories for nitrogen, helium, and argon during a 90 s unheated blowdown ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$). Helium yields the highest $I_{sp}$ due to its low molar mass, while argon produces the lowest.*

Study 3 contrasted unregulated blowdown against pressure-regulated operation at setpoints of $3.0\text{ MPa}$, $5.0\text{ MPa}$, and $8.0\text{ MPa}$. As summarized in Table 4 and Figure 4, unregulated thrust decayed rapidly from $51.11\text{ N}$ to $0.21\text{ N}$, whereas $3.0\text{ MPa}$ regulation capped peak thrust at $7.67\text{ N}$ while maintaining $98.1\%$ of the unregulated $\Delta v$ ($42.48\text{ m/s}$) and raising the minimum tank temperature from $61.7\text{ K}$ to $88.9\text{ K}$.

*Table 4. Comparison of unregulated blowdown and pressure-regulated thrust profiles for a 90 s nitrogen burn ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$, $T_0 = 295\text{ K}$).*

| Operating Mode | Peak Thrust [N] | Final Thrust [N] | Final $\Delta v$ [m/s] | Min Tank Temp [K] |
| :--- | :--- | :--- | :--- | :--- |
| Blowdown (Off) | 51.11 | 0.21 | 43.31 | 61.7 |
| Regulated (8.0 MPa) | 20.44 | 0.21 | 43.31 | 61.7 |
| Regulated (5.0 MPa) | 12.78 | 0.23 | 43.27 | 63.3 |
| Regulated (3.0 MPa) | 7.67 | 0.77 | 42.48 | 88.9 |

![Study 3](report_figures/study3_regulator_comparison.png)

*Figure 4. Instantaneous thrust profiles comparing unregulated nitrogen blowdown against 3.0 MPa, 5.0 MPa, and 8.0 MPa pressure-regulated modes ($V = 4.0\text{ L}$, $P_0 = 20.0\text{ MPa}$). Regulation stabilizes thrust at the expense of lower peak force and longer burn duration.*

Study 4 varied nozzle throat diameter from $0.8\text{ mm}$ to $2.4\text{ mm}$ during an adiabatic $90\text{ s}$ nitrogen blowdown. Table 5 and Figure 5 show that peak thrust scaled quadratically with throat diameter from $16.69\text{ N}$ ($d^* = 0.8\text{ mm}$) to $150.20\text{ N}$ ($d^* = 2.4\text{ mm}$). All five throat configurations crossed the $230\text{ K}$ valve-freezing threshold during a continuous $90\text{ s}$ adiabatic discharge, with diameters of $1.6\text{ mm}$ and larger reaching the $2\%$ residual-mass depletion floor at $61.7\text{ K}$ before $90\text{ s}$ elapsed.

*Table 5. Effect of nozzle throat diameter on peak thrust, total $\Delta v$, and adiabatic cooling during a 90 s nitrogen blowdown ($P_0 = 20.0\text{ MPa}$, $\dot{Q}_{\text{wall}} = 0\text{ W}$).*

| Throat $d^*$ [mm] | Peak Thrust [N] | Final $\Delta v$ [m/s] | Min Tank Temp [K] | Valve Freeze ($< 230\text{ K}$) |
| :--- | :--- | :--- | :--- | :--- |
| 0.8 | 16.69 | 39.02 | 138.7 | YES |
| 1.2 | 37.55 | 43.08 | 71.5 | YES |
| 1.6 | 66.75 | 43.31 | 61.7 | YES |
| 2.0 | 104.30 | 43.31 | 61.7 | YES |
| 2.4 | 150.20 | 43.31 | 61.7 | YES |

![Study 4](report_figures/study4_throat_freeze_risk.png)

*Figure 5. Tank temperature decay histories for nozzle throat diameters from 0.8 mm to 2.4 mm during an adiabatic 90 s nitrogen blowdown ($P_0 = 20.0\text{ MPa}$, $\dot{Q}_{\text{wall}} = 0\text{ W}$). Larger throats accelerate depressurization and reach the 61.7 K depletion floor earlier.*

Study 5 evaluated coast-phase thermal recovery during a $400\text{ km}$ to $450\text{ km}$ Hohmann transfer ($\Delta v_{\text{target}} = 28.17\text{ m/s}$, $t_{\text{coast}} = 46.4\text{ min}$) across ambient tank wall heat inputs from $0\text{ W}$ to $6.0\text{ W}$. As shown in Table 6 and Figure 6, every configuration achieved the full $28.17\text{ m/s}$ transfer, but heat inputs of $0\text{--}4.0\text{ W}$ resulted in minimum temperatures of $207.6\text{--}228.9\text{ K}$ (below the $230\text{ K}$ freeze limit). Increasing ambient wall heating to $6.0\text{ W}$ raised the minimum tank temperature to $239.6\text{ K}$ and improved remaining propellant margin from $41.5\%$ to $43.4\%$.

*Table 6. Effect of ambient tank wall heating on thermal recovery and propellant margin during a 400 km to 450 km nitrogen Hohmann transfer ($\dot{Q}_{\text{heater}} = 25\text{ W}$).*

| Wall Heat [W] | Achieved $\Delta v$ [m/s] | Min Tank Temp [K] | Final Tank Temp [K] | Propellant Left [%] |
| :--- | :--- | :--- | :--- | :--- |
| 0.0 | 28.17 | 207.6 | 207.6 | 41.5 |
| 1.0 | 28.17 | 212.9 | 212.9 | 41.9 |
| 2.0 | 28.17 | 218.2 | 218.2 | 42.2 |
| 4.0 | 28.17 | 228.9 | 228.9 | 42.8 |
| 6.0 | 28.17 | 239.6 | 239.6 | 43.4 |

![Study 5](report_figures/study5_coast_thermal_recovery.png)

*Figure 6. Tank temperature histories across Burn 1, the 46.4 min coast phase, and Burn 2 for ambient tank wall heat inputs from 0 W to 6.0 W ($400\text{ km}$ to $450\text{ km}$ Hohmann transfer, $\dot{Q}_{\text{heater}} = 25\text{ W}$). Ambient heating of 6.0 W maintains tank temperature above the 230 K valve-freezing limit throughout both burns.*

## 4. Discussion

The parametric results reveal clear physical trade-offs governing CubeSat propulsion design. In Study 1, electrical resistojet heating increased both $I_{sp}$ and total $\Delta v$ because exhaust velocity scales with $\sqrt{T_{0,\text{exit}}}$, as shown in Equation (11). Because the initial mass flow rate at $20.0\text{ MPa}$ is high ($\dot{m} \approx 0.07\text{ kg/s}$), heater powers of $25\text{--}50\text{ W}$ produced negligible temperature rise early in the burn (keeping peak $I_{sp}$ at $73.2\text{ s}$), whereas at $100\text{ W}$ the late-burn temperature boost elevated peak $I_{sp}$ to $80.5\text{ s}$ as $\dot{m}$ declined. Simultaneously, Equation (9) dictates that choked mass flow rate scales inversely with $\sqrt{T_{0,\text{exit}}}$, explaining why higher heater power slightly reduced propellant expenditure and moderated tank cooling.

Study 2 highlighted the competing effects of molar mass and storage density in volume-constrained spacecraft. Although helium produced the highest specific impulse ($169.4\text{ s}$) due to its large specific gas constant ($R = 2077.1\text{ J/(kg}\cdot\text{K)}$), Equation (5) dictates that its initial stored mass at $20.0\text{ MPa}$ and $4.0\text{ L}$ ($0.1306\text{ kg}$) is seven times smaller than that of nitrogen ($0.9137\text{ kg}$). Argon stored the largest mass ($1.3032\text{ kg}$), but its low exhaust velocity ($53.6\text{ s}$ peak $I_{sp}$) and higher specific heat ratio ($\gamma = 1.67$, causing steeper adiabatic cooling to $31.2\text{ K}$) reduced its total $\Delta v$ below that of nitrogen. Consequently, nitrogen provided the optimal balance between stored propellant mass and exhaust velocity for moderate-$\Delta v$ low-Earth-orbit maneuvers.

Studies 3 through 5 demonstrated the operational coupling between transient tank thermodynamics and SSSF nozzle performance. Pressure regulation at $3.0\text{ MPa}$ reduced peak thrust by $85\%$ relative to blowdown for simplified attitude control while sacrificing less than $2\%$ of total $\Delta v$, at the cost of throttling irreversibility ($\dot{S}_{\text{gen,reg}} > 0$). In Study 4, continuous $90\text{ s}$ adiabatic blowdowns drove all tested throat sizes below $230\text{ K}$, confirming that finite-duration burns must either be duty-cycled or thermally assisted. In Study 5, the $46.4\text{ min}$ Hohmann coast phase decoupled SSSF flow from transient heat transfer, enabling $6.0\text{ W}$ of ambient wall heating to recover tank temperature prior to Burn 2, maintain $T \ge 239.6\text{ K}$, and improve remaining propellant margin by $1.9$ percentage points via higher second-burn $I_{sp}$.

Several modeling assumptions bound the applicability of these results. Treating propellants as ideal gases neglects real-gas compressibility ($Z \ne 1$) at storage pressures of $20\text{--}35\text{ MPa}$, which slightly alters initial stored mass and introduces Joule-Thomson cooling across the pressure regulator. Additionally, the lumped-capacitance tank model assumes spatially uniform gas temperature and neglects transient conductive heat losses through the nozzle walls during short pulses.

## 5. Conclusions

An integrated transient-tank and SSSF-nozzle thermodynamic simulation was formulated, verified to within $10^{-10}$ relative error against First Law, Second Law, analytical, and solver-convergence benchmarks, and deployed in an interactive virtual laboratory. Parametric investigations established that nitrogen maximizes total $\Delta v$ ($43.31\text{ m/s}$) in a volume-constrained $4.0\text{ L}$ tank, pressure regulation stabilizes thrust with minimal $\Delta v$ penalty, and continuous adiabatic blowdowns rapidly violate the $230\text{ K}$ valve-freezing threshold. For a $12.0\text{ kg}$ CubeSat executing a $400\text{ km}$ to $450\text{ km}$ Hohmann transfer ($\Delta v = 28.17\text{ m/s}$), pairing nitrogen propellant with $25\text{ W}$ of resistojet heating and $6.0\text{ W}$ of coast-phase tank wall heating satisfies all orbital and thermal constraints with $43.4\%$ propellant margin remaining.

## References

[1] M. J. Moran, H. N. Shapiro, D. D. Boettner, and M. B. Bailey, *Fundamentals of Engineering Thermodynamics*, 9th ed. Hoboken, NJ, USA: Wiley, 2018.

[2] G. P. Sutton and O. Biblarz, *Rocket Propulsion Elements*, 9th ed. Hoboken, NJ, USA: Wiley, 2017.

[3] P. Virtanen et al., "SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python," *Nature Methods*, vol. 17, pp. 261–272, 2020.