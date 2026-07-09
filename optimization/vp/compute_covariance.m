%% Compute Power Covariance Matrix (Step 4)
%
% Reconstructs power timeseries for candidate sites, computes the
% covariance matrix needed for the portfolio optimization objective.
%
% Input:  ../results/candidates.nc  (from 03_screen_candidates.py)
%         ../results/harmonics.nc   (from 01_extract_harmonics.py)
% Output: ../results/covariance.nc
%
% Requires: T_TIDE v1.5beta, Parallel Computing Toolbox

clear; close all; clc;

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir), scriptDir = pwd; end

%% Paths
addpath(fullfile(scriptDir, 'config'));

ttideDir = fullfile(scriptDir, 't_tide');
if ~exist('t_predic', 'file')
    addpath(ttideDir);
    fprintf('Added T_TIDE: %s\n', ttideDir);
end

envResults = getenv('TIDAL_RESULTS_DIR');
if ~isempty(envResults)
    resultsDir = envResults;
else
    envGroup = getenv('TIDAL_GROUP');
    envState = getenv('TIDAL_STATE');
    if ~isempty(envGroup)
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'vp', 'groups', envGroup);
    elseif ~isempty(envState) && ~contains(envState, ',')
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'vp', 'states', envState);
    else
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'vp', 'groups', 'pooled');
    end
end
if ~exist(resultsDir, 'dir'), mkdir(resultsDir); end
fprintf('Results dir: %s\n', resultsDir);

% harmonics.nc is resource-only (identical across every power curve); read it
% from the shared resource dir when set, else from resultsDir (single-dir runs).
envResource = getenv('TIDAL_RESOURCE_DIR');
if ~isempty(envResource), resourceDir = envResource; else, resourceDir = resultsDir; end

% candidates.nc / covariance.nc are curve-level (shared across capacities
% within a power curve); they live in the shared curve dir when set, else in
% resultsDir.
envCurve = getenv('TIDAL_CURVE_DIR');
if ~isempty(envCurve), curveDir = envCurve; else, curveDir = resultsDir; end
if ~exist(curveDir, 'dir'), mkdir(curveDir); end

candidatesFile = fullfile(curveDir, 'candidates.nc');
harmonicsFile  = fullfile(resourceDir, 'harmonics.nc');
outputFile     = fullfile(curveDir, 'covariance.nc');

if exist(outputFile, 'file')
    fprintf('Already exists: %s\nDelete to re-run.\n', outputFile);
    return;
end

%% VP Gen5 power curve (Lewis et al. 2021)
cfg = config();

RHO      = cfg.RHO;
AREA     = cfg.AREA;
CP       = cfg.CP;
V_CUT_IN = cfg.V_CUT_IN;
V_RATED  = cfg.V_RATED;
P_RATED  = cfg.P_RATED;

fprintf('Power curve: cut-in=%.2f, rated=%.2f m/s, P_rated=%.0f W\n', ...
    V_CUT_IN, V_RATED, P_RATED);

%% Load candidates
fprintf('\nLoading candidates: %s\n', candidatesFile);
point_index = ncread(candidatesFile, 'point_index');  % 0-based index into harmonics.nc
lat_cand    = ncread(candidatesFile, 'latitude');

n_cand = length(point_index);
fprintf('  %d candidates\n', n_cand);

%% Load ellipse parameters for candidates from harmonics
fprintf('Loading harmonics: %s\n', harmonicsFile);
cmaj_full = ncread(harmonicsFile, 'current_semimajor');
cmin_full = ncread(harmonicsFile, 'current_semiminor');
cinc_full = ncread(harmonicsFile, 'current_inclination');
cpha_full = ncread(harmonicsFile, 'current_phase');

% NetCDF stores (constituent x point); transpose to (point x constituent)
if size(cmaj_full, 1) == 10
    cmaj_full = cmaj_full';
    cmin_full = cmin_full';
    cinc_full = cinc_full';
    cpha_full = cpha_full';
end

% Extract only candidate rows (point_index is 0-based, MATLAB is 1-based)
idx = point_index + 1;
cmaj = cmaj_full(idx, :);
cmin = cmin_full(idx, :);
cinc = cinc_full(idx, :);
cpha = cpha_full(idx, :);
clear cmaj_full cmin_full cinc_full cpha_full;

% Skip P1 (index 3), use 9 valid constituents
valid_idx = cfg.valid_idx;
valid_names = cfg.valid_names;
n_con = length(valid_names);

cmaj = cmaj(:, valid_idx);
cmin = cmin(:, valid_idx);
cinc = cinc(:, valid_idx);
cpha = cpha(:, valid_idx);

fprintf('  Extracted ellipse params: %d sites x %d constituents\n', n_cand, n_con);

%% Match constituents to T_TIDE
const = t_getconsts;
name_input = char(zeros(n_con, 4));
f = zeros(n_con, 1);

for k = 1:n_con
    idx_k = strmatch(valid_names{k}, const.name);
    name_input(k, :) = const.name(idx_k, :);
    f(k) = const.freq(idx_k);
end
fprintf('  Matched %d constituents to T_TIDE\n', n_con);

%% Time vector (year 2013, 1-hour)
t = (cfg.tmin : cfg.dt : cfg.tmax)';
n_times = length(t);
fprintf('\nTime: %s to %s, %d steps\n', datestr(cfg.tmin), datestr(cfg.tmax), n_times);

%% Reconstruct power timeseries (parallel)
pool = gcp('nocreate');
if isempty(pool), pool = parpool('Threads', 8); end
fprintf('Using %d workers for %d candidates\n\n', pool.NumWorkers, n_cand);

power_matrix = zeros(n_times, n_cand, 'single');
skipped = false(n_cand, 1);

timer = tic;

parfor i = 1:n_cand
    major = cmaj(i, :)';
    minor = cmin(i, :)';
    inc   = cinc(i, :)';
    pha   = cpha(i, :)';

    if all(isnan(major))
        skipped(i) = true;
        continue;
    end

    major(isnan(major)) = 0;
    minor(isnan(minor)) = 0;
    inc(isnan(inc)) = 0;
    pha(isnan(pha)) = 0;

    zer = zeros(n_con, 1);
    tidecon_v = [major, zer, minor, zer, inc, zer, pha, zer];
    v_pred = t_predic(t, name_input, f, tidecon_v, 'latitude', lat_cand(i));

    speed = abs(v_pred);

    % Apply power curve
    power = zeros(n_times, 1, 'single');
    cubic = (speed >= V_CUT_IN) & (speed <= V_RATED);
    power(cubic) = single(0.5 * RHO * AREA * CP * speed(cubic).^3);
    rated = (speed > V_RATED);
    power(rated) = single(P_RATED);

    power_matrix(:, i) = power;
end

elapsed_recon = toc(timer);
n_skipped = sum(skipped);
fprintf('Reconstruction: %.1f minutes, %d processed, %d skipped\n', ...
    elapsed_recon/60, n_cand - n_skipped, n_skipped);
fprintf('  Power matrix: %d x %d (%.0f MB)\n', ...
    n_times, n_cand, n_times * n_cand * 4 / 1e6);

%% Compute covariance matrix
fprintf('\nComputing covariance (%d x %d)...\n', n_cand, n_cand);
timer_cov = tic;

Sigma = cov(double(power_matrix));

elapsed_cov = toc(timer_cov);
fprintf('  Done in %.1f seconds\n', elapsed_cov);
fprintf('  Size: %.1f MB\n', numel(Sigma) * 8 / 1e6);
fprintf('  Symmetric: %s\n', mat2str(issymmetric(Sigma)));
fprintf('  Variance range: [%.2f, %.2f] W^2\n', min(diag(Sigma)), max(diag(Sigma)));

%% Save NetCDF
fprintf('\nSaving: %s\n', outputFile);

if exist(outputFile, 'file'), delete(outputFile); end

nccreate(outputFile, 'covariance', ...
    'Dimensions', {'site_i', n_cand, 'site_j', n_cand}, ...
    'Datatype', 'double', 'DeflateLevel', 4);

ncwrite(outputFile, 'covariance', Sigma);

ncwriteatt(outputFile, 'covariance', 'units', 'W^2');
ncwriteatt(outputFile, 'covariance', 'long_name', 'Power output covariance matrix');

ncwriteatt(outputFile, '/', 'title', 'Covariance matrix of tidal power output');
ncwriteatt(outputFile, '/', 'source', 'T_TIDE t_predic from ROMS harmonics');
ncwriteatt(outputFile, '/', 'n_candidates', int32(n_cand));
ncwriteatt(outputFile, '/', 'n_timesteps', int32(n_times));
ncwriteatt(outputFile, '/', 'reconstruction_year', '2013');
ncwriteatt(outputFile, '/', 'time_step_hours', int32(1));
ncwriteatt(outputFile, '/', 'power_curve', sprintf('VP Gen5 Lewis: Cp=%.2f, Vci=%.2f, Vr=%.2f m/s', CP, V_CUT_IN, V_RATED));
ncwriteatt(outputFile, '/', 'P_rated_W', P_RATED);
ncwriteatt(outputFile, '/', 'constituents', strjoin(valid_names, ', '));
ncwriteatt(outputFile, '/', 'created', datestr(now, 'yyyy-mm-ddTHH:MM:SS'));

file_info = dir(outputFile);
fprintf('Saved: %.1f MB\n', file_info.bytes / 1e6);
fprintf('Total time: %.1f minutes\n', (elapsed_recon + elapsed_cov) / 60);
