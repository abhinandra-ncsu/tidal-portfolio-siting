# Optimization Cost Structure

How CapEx and OpEx components feed into the optimization's LCOE constraint. Costs are split into two categories based on whether they depend on which sites are selected.

See `capex/capex_cost_components.md` and `opex/opex_cost_components.md` for how each component is computed.

---

## Project-Level Constant — C_const(N)

Costs that depend only on the number of TriFrames (N), not on which sites are chosen.

**CapEx components:**

| Component | Formula | Why constant |
|-----------|---------|-------------|
| Device manufacturing | Σ C_device × i^b, i=1..N (learning curve, b = ln(0.88)/ln(2)) | Depends on N only |
| Device installation | (2 + 1.5×N + 2) days × $33,647/day | Placement time scales with N only |
| Subsystem integration | 10% × C_device_total | Derived from device cost (N only) |

**OpEx components (per TriFrame, annual):**

| Component | Value | Why constant |
|-----------|-------|-------------|
| Replacement | $74,804/yr × N | Fixed per TriFrame |
| Repair | $37,619/yr × N | Fixed per TriFrame ($4,355 vessel + $33,264 labor) |

**Note:** Contingency, environmental compliance, and insurance have both constant and portfolio-dependent parts — see below.

---

## Portfolio-Dependent — c_site_i

Costs that change based on which sites are selected. All portfolio-dependent costs are functions of shore distance (d_i), making them linear in the decision variables x_i.

**CapEx components:**

| Component | Depends on | How |
|-----------|-----------|-----|
| Cable purchase | d_i | Nakhai (2023) Eq. 3 × d_i × 1000 m/km, per selected cable spec |
| Cable installation | d_i | Mattia per-meter metric: 160.67 €/m × 1.08 × d_i × 1000 ≈ $173,500 × d_i (km) |
| Contingency (partial) | d_i | 10% of (device + subsys + C_inst); inherits the cable-phase installation cost |
| Environmental compliance (partial) | d_i | 5% of (device + subsys + contingency); cascades from installation |

**OpEx components:**

| Component | Depends on | How |
|-----------|-----------|-----|
| Insurance (partial) | d_i | 1% of CapEx, which includes portfolio-dependent CapEx |

### Cascade

Installation has two parts that both feed the cascade:

```
C_inst = C_inst_device(N)              +  C_inst_cable(L_total)
         [constant: (2+1.5N+2)×$33,647]    [portfolio-dep: ≈ $173,500 × L_total]
              │                                    │
              ▼                                    ▼
Contingency = 10% × (C_device_total + C_subsys + C_inst)
              │                                    │
              ▼                                    ▼
Env. compliance = 5% × (C_device_total + C_subsys + C_contin)
              │                                    │
              ▼                                    ▼
CapEx total = C_device_total + C_elec + C_inst + C_subsys + C_contin + C_EC
              │                                    │
              ▼                                    ▼
Insurance = 1% × CapEx
```

Every cascade step is linear, so it splits cleanly into a constant part (left column → C_const(N)) and a portfolio-dependent part (right column → c_site_i). The portfolio-dependent piece per site i can be precomputed as a function of d_i and the selected cable specification before the optimization runs.

---

## Annualization

CapEx is annualized using the fixed charge rate (FCR):

```
FCR = 0.113 (11.3%)
```

OpEx is already annual.

Total annualized cost:

```
C_annual = FCR × CapEx + OpEx
         = C_const(N) + Σ_i x_i × c_site_i
```

where C_const(N) includes the annualized constant CapEx and the constant OpEx, and c_site_i includes the annualized portfolio-dependent CapEx and the portfolio-dependent OpEx (insurance) for site i.

---

## How This Enters the Optimization

The LCOE constraint in the optimization formulation:

```
C_const(N) + Σ_i x_i × (c_site_i - L × E_i) ≤ 0
```

- C_const(N) is a scalar, precomputed from N
- c_site_i is a per-site scalar, precomputed from d_i
- E_i is annual energy delivered at site i (see `energy/methodology.md`)
- L is the LCOE target

Since C_const(N), c_site_i, and E_i are all precomputed, the constraint is linear in x_i.
