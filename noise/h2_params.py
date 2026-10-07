"""H2 error-rate parameters for the local noise proxy.

Source: Quantinuum System Model H2 Product Data Sheet, version 2.00, 15 October 2024
(https://docs.quantinuum.com/systems/data_sheets/Quantinuum%20H2%20Product%20Data%20Sheet.pdf),
read on 6 October 2026. "Typical" and "minimum" columns as printed there.
These are data-sheet figures for the H2 hardware, not the H2-2E emulator's internal
model, and the sheet predates the H2-2 upgrade; treat as provisional until H2-2E
runs replace the proxy.
"""
H2_TYPICAL = dict(p1=3e-5, p2=1.5e-3, p_spam=1.5e-3, p_memory=5e-4, p_crosstalk=1e-5)
H2_MINIMUM = dict(p1=1e-5, p2=1.3e-3, p_spam=1e-3, p_memory=2e-4, p_crosstalk=1e-6)

# H2-2E emulator defaults as published on
# https://docs.quantinuum.com/systems/user_guide/emulator_user_guide/emulators/h2_emulators.html
# (table "H2-2E"; the page's sub-heading dates the model "from 2025-07-16"),
# transcribed in docs/platform_notes.md section 3.3 (read 2026-10-06).  These are
# the emulator's own default error parameters, not hardware data-sheet figures.
# Keys used by dm_sim.NoiseModel: p1, p2, p_meas_0, p_meas_1, p_init.  The other
# entries are recorded for completeness and are NOT modelled by dm_sim
# (emission/leakage branch, crosstalk, duration-based dephasing, RZZ angle scaling).
H2_2E_EMULATOR = dict(
    p1=7.3e-5,                     # 1-Qubit Fault Probability
    p2=1.29e-3,                    # 2-Qubit Fault Probability (at theta = pi/2)
    p_meas_0=9e-4,                 # bit flip when the outcome is 0 (0 read as 1)
    p_meas_1=1.8e-3,               # bit flip when the outcome is 1 (1 read as 0)
    p_init=4e-5,                   # Initialization Fault Probability
    p_crosstalk_meas=8.8e-6,       # not modelled
    p_crosstalk_init=9.6e-6,       # not modelled
    p1_emission_ratio=0.32,        # not modelled
    p2_emission_ratio=0.59,        # not modelled
    quadratic_dephasing_rate=0.043,    # not modelled (needs gate durations)
    linear_dephasing_rate=0.0028,      # not modelled (needs gate durations)
    coherent_to_incoherent_factor=2.0,  # not modelled
    przz_a=1.518, przz_b=0.241, przz_c=1.518, przz_d=0.241, przz_power=1.0,  # not modelled
)
