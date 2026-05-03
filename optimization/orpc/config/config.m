function cfg = config()
% CONFIG  Centralized parameters for the ORPC MATLAB pipeline scripts.
%
% Both build_histograms.m and compute_covariance.m call cfg = config()
% instead of defining their own copies.
%
% Sources documented inline; see ../methodology/ for full derivations.

    % ORPC TidGen 2.0 turbine (turbine_design_specification.md)
    cfg.RHO          = 1025.0;     % seawater density (kg/m^3)
    cfg.V_CUT_IN     = 0.5;        % cut-in (m/s)
    cfg.V_RATED      = 3.0;        % rated speed (m/s)
    cfg.V_PLATEAU_END = 3.5;       % zero past this (max operational)
    cfg.P_RATED      = 500000.0;   % rated electrical power (W)

    % SCM-tabulated electrical power curve (D7.2.8 SCM workbook,
    % `CEC Resource and Power` sheet column F, rows 12-42).
    % Speeds in m/s, power in W (= kW * 1000).
    cfg.SCM_SPEEDS  = (0:0.1:3.0)';
    cfg.SCM_POWER_W = 1000 * [
        0.0;           % 0.0
        0.0;           % 0.1
        0.0;           % 0.2
        0.0;           % 0.3
        0.0;           % 0.4
        2.74828125;    % 0.5
        4.74903;       % 0.6
        7.54128375;    % 0.7
        11.25696;      % 0.8
        16.02797625;   % 0.9
        21.98625;      % 1.0
        29.26369875;   % 1.1
        37.99224;      % 1.2
        48.30379125;   % 1.3
        60.33027;      % 1.4
        74.20359375;   % 1.5
        90.05568;      % 1.6
        108.01844625;  % 1.7
        128.22381;     % 1.8
        150.80368875;  % 1.9
        175.89;        % 2.0
        203.61466125;  % 2.1
        234.10959;     % 2.2
        267.50670375;  % 2.3
        303.93792;     % 2.4
        338.56064564;  % 2.5
        371.97404738;  % 2.6
        404.66591768;  % 2.7
        436.71356348;  % 2.8
        468.18362869;  % 2.9
        499.13387137;  % 3.0
    ];

    % Tidal constituents - P1 (index 3) is all NaN in ROMS, skip it
    cfg.valid_idx   = [1, 2, 4, 5, 6, 7, 8, 9, 10];
    cfg.valid_names = {'Q1', 'O1', 'K1', 'N2', 'M2', 'S2', 'K2', 'M4', 'M6'};

    % Reconstruction time range - year 2013, 1-hour resolution
    cfg.tmin = datenum(2013, 1, 1, 0, 0, 0);
    cfg.tmax = datenum(2013, 12, 31, 23, 0, 0);
    cfg.dt   = 1/24;

end
