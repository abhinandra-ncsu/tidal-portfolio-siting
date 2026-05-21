function cfg = config()
% CONFIG  Centralized parameters for the MATLAB tidal pipeline scripts.
%
% Both build_histograms.m and compute_covariance.m call cfg = config()
% instead of defining their own copies.
%
% Sources documented inline; see docs/ for full derivations.

    % VP turbine — variant family (experiments/turbine_modification/EXPERIMENT.md)
    variant = getenv('TIDAL_VARIANT');
    if isempty(variant); variant = 'gen5'; end
    cfg.VARIANT = lower(variant);

    cfg.RHO = 1025.0;     % seawater density (kg/m^3)
    cfg.CP  = 0.37;       % power coefficient (Lewis et al. 2021, held across family)

    switch cfg.VARIANT
        case 'gen5'
            cfg.AREA = 19.63; cfg.V_CUT_IN = 0.61; cfg.V_RATED = 2.03; cfg.P_RATED = 31200.0;
        case 'modvp4'
            cfg.AREA = 12.57; cfg.V_CUT_IN = 0.70; cfg.V_RATED = 2.33; cfg.P_RATED = 30100.0;
        case 'modvp3'
            cfg.AREA =  7.07; cfg.V_CUT_IN = 0.70; cfg.V_RATED = 2.32; cfg.P_RATED = 16800.0;
        case 'modvp2'
            cfg.AREA =  3.14; cfg.V_CUT_IN = 0.67; cfg.V_RATED = 2.22; cfg.P_RATED =  6500.0;
        otherwise
            error('config:UnknownVariant', ...
                  'Unknown TIDAL_VARIANT=%s; expected one of gen5/modvp4/modvp3/modvp2', cfg.VARIANT);
    end

    % Tidal constituents — P1 (index 3) is all NaN in ROMS, skip it
    cfg.valid_idx   = [1, 2, 4, 5, 6, 7, 8, 9, 10];
    cfg.valid_names = {'Q1', 'O1', 'K1', 'N2', 'M2', 'S2', 'K2', 'M4', 'M6'};

    % Reconstruction time range — year 2013, 1-hour resolution
    cfg.tmin = datenum(2013, 1, 1, 0, 0, 0);
    cfg.tmax = datenum(2013, 12, 31, 23, 0, 0);
    cfg.dt   = 1/24;  % hours -> days

end
