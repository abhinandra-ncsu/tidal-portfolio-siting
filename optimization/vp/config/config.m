function cfg = config()
% CONFIG  Centralized parameters for the MATLAB tidal pipeline scripts.
%
% Both build_histograms.m and compute_covariance.m call cfg = config()
% instead of defining their own copies.
%
% Sources documented inline; see docs/ for full derivations.

    % VP Gen5 turbine (Lewis et al. 2021)
    cfg.RHO      = 1025.0;     % seawater density (kg/m^3)
    cfg.AREA     = 19.63;      % swept area (m^2), D = 5 m
    cfg.CP       = 0.37;       % power coefficient (system Cp)
    cfg.V_CUT_IN = 0.63;       % cut-in speed (m/s)
    cfg.V_RATED  = 2.11;       % rated speed (m/s)
    cfg.P_RATED  = 35000.0;    % rated power per turbine (W)

    % Tidal constituents — P1 (index 3) is all NaN in ROMS, skip it
    cfg.valid_idx   = [1, 2, 4, 5, 6, 7, 8, 9, 10];
    cfg.valid_names = {'Q1', 'O1', 'K1', 'N2', 'M2', 'S2', 'K2', 'M4', 'M6'};

    % Reconstruction time range — year 2013, 1-hour resolution
    cfg.tmin = datenum(2013, 1, 1, 0, 0, 0);
    cfg.tmax = datenum(2013, 12, 31, 23, 0, 0);
    cfg.dt   = 1/24;  % hours -> days

end
