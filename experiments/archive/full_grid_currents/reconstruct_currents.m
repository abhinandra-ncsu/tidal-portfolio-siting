%% Reconstruct hourly currents and pool into one speed histogram (Step 2)
%
% Reconstructs a 1-year (2013, hourly) tidal current timeseries for each site
% using T_TIDE's t_predic, and pools EVERY hourly speed value (every site x
% every hour) into a single count histogram. The histogram of the actual
% reconstructed data is what Step 3 plots.
%
% Self-contained for the full_grid_currents experiment: writes into this
% folder's results/ and pulls shared config + T_TIDE from optimization/vp.
%
% Input:  results/sites.nc            (from 01_extract.py - full grid, no depth filter)
% Output: results/speed_histogram.nc
%
% Requires: T_TIDE v1.5beta, Parallel Computing Toolbox

clear; close all; clc;

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir), scriptDir = pwd; end

%% Paths - shared config + T_TIDE live under optimization/vp
repoRoot = fileparts(fileparts(scriptDir));
vpDir = fullfile(repoRoot, 'optimization', 'vp');
addpath(fullfile(vpDir, 'config'));
if ~exist('t_predic', 'file')
    addpath(fullfile(vpDir, 't_tide'));
    fprintf('Added T_TIDE: %s\n', fullfile(vpDir, 't_tide'));
end

resultsDir = fullfile(scriptDir, 'results');
if ~exist(resultsDir, 'dir'), mkdir(resultsDir); end
fprintf('Results dir: %s\n', resultsDir);
inputFile  = fullfile(resultsDir, 'sites.nc');
outputFile = fullfile(resultsDir, 'speed_histogram.nc');

if exist(outputFile, 'file')
    fprintf('Already exists: %s\nDelete to re-run.\n', outputFile);
    return;
end

% Verify-first knob: 0 = all sites; set >0 to pool a random subset and
% sanity-check the shape + extrapolate runtime before the full run.
nSample = 0;

%% Parameters
cfg = config();

edges = 0.0 : 0.05 : 5.0;   % 101 edges -> 100 bins, 0-5 m/s
n_bins = length(edges) - 1;
bin_centers = edges(1:end-1) + 0.025;

% Year 2013, 1-hour resolution (matches build_histograms.m)
t = (cfg.tmin : cfg.dt : cfg.tmax)';
n_times = length(t);
fprintf('Time: %s to %s, %d steps\n', datestr(cfg.tmin), datestr(cfg.tmax), n_times);

%% Read harmonics
fprintf('Reading: %s\n', inputFile);
cmaj  = ncread(inputFile, 'current_semimajor');
cmin  = ncread(inputFile, 'current_semiminor');
cinc  = ncread(inputFile, 'current_inclination');
cpha  = ncread(inputFile, 'current_phase');
lat   = ncread(inputFile, 'latitude');

% NetCDF stores (constituent x point); transpose to (point x constituent)
if size(cmaj, 1) == 10
    cmaj = cmaj';
    cmin = cmin';
    cinc = cinc';
    cpha = cpha';
end

n_all = length(lat);
fprintf('  %d points, %d constituents\n', n_all, size(cmaj, 2));

% Optional subset for verify-first
if nSample > 0 && nSample < n_all
    rng(0);
    sel = sort(randperm(n_all, nSample))';
    fprintf('  SUBSET: pooling %d of %d sites (nSample)\n', nSample, n_all);
else
    sel = (1:n_all)';
end
cmaj = cmaj(sel, :);  cmin = cmin(sel, :);  cinc = cinc(sel, :);  cpha = cpha(sel, :);
lat = lat(sel);
n_pts = length(lat);

% P1 (index 3) is all NaN - skip it, use remaining 9
valid_idx = cfg.valid_idx;
valid_names = cfg.valid_names;
n_con = length(valid_names);

cmaj = cmaj(:, valid_idx);
cmin = cmin(:, valid_idx);
cinc = cinc(:, valid_idx);
cpha = cpha(:, valid_idx);

%% Match constituents to T_TIDE frequency table
const = t_getconsts;
name_input = char(zeros(n_con, 4));
f = zeros(n_con, 1);

for k = 1:n_con
    idx = strmatch(valid_names{k}, const.name);
    name_input(k, :) = const.name(idx, :);
    f(k) = const.freq(idx);
end
fprintf('  Matched %d constituents to T_TIDE\n', n_con);

%% Reconstruct speeds, pool all hourly values into one histogram (parallel)
pool = gcp('nocreate');
if isempty(pool), pool = parpool; end
fprintf('Using %d workers for %d points\n\n', pool.NumWorkers, n_pts);

hist_total = zeros(1, n_bins);   % reduction: summed counts across all sites
skipped    = false(n_pts, 1);

timer = tic;

parfor i = 1:n_pts
    major = cmaj(i, :)';
    minor = cmin(i, :)';
    inc   = cinc(i, :)';
    pha   = cpha(i, :)';

    % Skip points with no valid harmonics (contribute nothing)
    if all(isnan(major))
        skipped(i) = true;
        continue;
    end

    % Zero out individual NaN constituents (partial data)
    major(isnan(major)) = 0;
    minor(isnan(minor)) = 0;
    inc(isnan(inc)) = 0;
    pha(isnan(pha)) = 0;

    % T_TIDE tidecon format: [major, err, minor, err, inc, err, pha, err]
    zer = zeros(n_con, 1);
    tidecon_v = [major, zer, minor, zer, inc, zer, pha, zer];
    v_pred = t_predic(t, name_input, f, tidecon_v, 'latitude', lat(i));

    speed = abs(v_pred);
    hist_total = hist_total + histcounts(speed, edges);
end

elapsed = toc(timer);
n_skipped = sum(skipped);
total_binned = sum(hist_total);
expected = (n_pts - n_skipped) * n_times;
fprintf('Done: %.2f hours, %d processed, %d skipped\n', ...
    elapsed/3600, n_pts - n_skipped, n_skipped);
fprintf('  Binned %d of %d expected site-hours (%.4f%% in 0-5 m/s range)\n', ...
    total_binned, expected, 100 * total_binned / expected);

%% Save NetCDF
fprintf('\nSaving: %s\n', outputFile);
if exist(outputFile, 'file'), delete(outputFile); end

nccreate(outputFile, 'count', 'Dimensions', {'speed_bin', n_bins}, 'Datatype', 'double');
nccreate(outputFile, 'speed_bin_edges',   'Dimensions', {'edge', n_bins + 1}, 'Datatype', 'double');
nccreate(outputFile, 'speed_bin_centers', 'Dimensions', {'speed_bin', n_bins}, 'Datatype', 'double');

ncwrite(outputFile, 'count', hist_total(:));
ncwrite(outputFile, 'speed_bin_edges',   edges);
ncwrite(outputFile, 'speed_bin_centers', bin_centers);

ncwriteatt(outputFile, 'count',           'units', 'count of site-hours');
ncwriteatt(outputFile, 'speed_bin_edges', 'units', 'm/s');
ncwriteatt(outputFile, 'speed_bin_centers', 'units', 'm/s');

ncwriteatt(outputFile, '/', 'title', 'Pooled hourly tidal current speed histogram - US East Coast, full grid (no depth filter)');
ncwriteatt(outputFile, '/', 'source', 'T_TIDE t_predic from ROMS harmonics (Pawlowicz et al., 2002)');
ncwriteatt(outputFile, '/', 'reconstruction_year', '2013');
ncwriteatt(outputFile, '/', 'time_step_hours', int32(1));
ncwriteatt(outputFile, '/', 'n_time_steps', int32(n_times));
ncwriteatt(outputFile, '/', 'n_points', int32(n_pts));
ncwriteatt(outputFile, '/', 'n_skipped', int32(n_skipped));
ncwriteatt(outputFile, '/', 'n_sample', int32(nSample));
ncwriteatt(outputFile, '/', 'total_site_hours_binned', total_binned);
ncwriteatt(outputFile, '/', 'constituents', strjoin(valid_names, ', '));
ncwriteatt(outputFile, '/', 'created', datestr(now, 'yyyy-mm-ddTHH:MM:SS'));

file_info = dir(outputFile);
fprintf('Saved: %.3f MB\n', file_info.bytes / 1e6);
fprintf('Total time: %.2f hours\n', elapsed / 3600);
