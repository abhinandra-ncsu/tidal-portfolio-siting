%% Build Speed Histograms from Tidal Harmonics (Step 2)
%
% Reconstructs 1-year tidal current timeseries for each point using
% T_TIDE's t_predic, bins speeds into probability histograms.
%
% Input:  ../results/harmonics.nc  (from 01_extract_harmonics.py)
% Output: ../results/histograms.nc
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
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'orpc', 'groups', envGroup);
    elseif ~isempty(envState) && ~contains(envState, ',')
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'orpc', 'states', envState);
    else
        resultsDir = fullfile(scriptDir, '..', '..', 'results', 'orpc', 'groups', 'pooled');
    end
end
if ~exist(resultsDir, 'dir'), mkdir(resultsDir); end
fprintf('Results dir: %s\n', resultsDir);
inputFile  = fullfile(resultsDir, 'harmonics.nc');
outputFile = fullfile(resultsDir, 'histograms.nc');

if exist(outputFile, 'file')
    fprintf('Already exists: %s\nDelete to re-run.\n', outputFile);
    return;
end

%% Parameters
cfg = config();

edges = 0.0 : 0.05 : 5.0;   % 101 edges -> 100 bins, 0-5 m/s
n_bins = length(edges) - 1;
bin_centers = edges(1:end-1) + 0.025;

% Year 2013, 1-hour resolution
% M6 (fastest constituent) has ~4.14 hr period -> ~4 samples/cycle
t = (cfg.tmin : cfg.dt : cfg.tmax)';
n_times = length(t);
fprintf('Time: %s to %s, %d steps\n', datestr(cfg.tmin), datestr(cfg.tmax), n_times);

%% Read harmonics
fprintf('Reading: %s\n', inputFile);
cmaj = ncread(inputFile, 'current_semimajor');
cmin = ncread(inputFile, 'current_semiminor');
cinc = ncread(inputFile, 'current_inclination');
cpha = ncread(inputFile, 'current_phase');
lat  = ncread(inputFile, 'latitude');
lon  = ncread(inputFile, 'longitude');
depth = ncread(inputFile, 'depth');

% NetCDF stores (constituent x point); transpose to (point x constituent)
if size(cmaj, 1) == 10
    cmaj = cmaj';
    cmin = cmin';
    cinc = cinc';
    cpha = cpha';
end

n_pts = length(lat);
fprintf('  %d points, %d constituents\n', n_pts, size(cmaj, 2));

% P1 (index 3) is all NaN — skip it, use remaining 9
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

%% Reconstruct speeds and build histograms (parallel)
pool = gcp('nocreate');
if isempty(pool), pool = parpool('Threads', 8); end  % Threads: process pool fails on this box (worker shut down status 1)
fprintf('Using %d workers for %d points\n\n', pool.NumWorkers, n_pts);

histograms  = zeros(n_pts, n_bins);
max_speeds  = zeros(n_pts, 1);
mean_speeds = zeros(n_pts, 1);
skipped     = false(n_pts, 1);

timer = tic;

parfor i = 1:n_pts
    major = cmaj(i, :)';
    minor = cmin(i, :)';
    inc   = cinc(i, :)';
    pha   = cpha(i, :)';

    % Skip points with no valid harmonics
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

    histograms(i, :) = histcounts(speed, edges, 'Normalization', 'probability');
    max_speeds(i)  = max(speed);
    mean_speeds(i) = mean(speed);
end

elapsed = toc(timer);
n_skipped = sum(skipped);
fprintf('Done: %.1f hours, %d processed, %d skipped\n', ...
    elapsed/3600, n_pts - n_skipped, n_skipped);
fprintf('  Mean speed: %.4f m/s, Max speed: %.4f m/s\n', ...
    mean(mean_speeds(~skipped)), max(max_speeds));

%% Save NetCDF
fprintf('\nSaving: %s\n', outputFile);

if exist(outputFile, 'file'), delete(outputFile); end

nccreate(outputFile, 'latitude',   'Dimensions', {'point', n_pts}, 'Datatype', 'double');
nccreate(outputFile, 'longitude',  'Dimensions', {'point', n_pts}, 'Datatype', 'double');
nccreate(outputFile, 'depth',      'Dimensions', {'point', n_pts}, 'Datatype', 'single');
nccreate(outputFile, 'speed_histogram', ...
    'Dimensions', {'point', n_pts, 'speed_bin', n_bins}, ...
    'Datatype', 'single', 'DeflateLevel', 4);
nccreate(outputFile, 'speed_bin_edges',   'Dimensions', {'edge', n_bins + 1}, 'Datatype', 'double');
nccreate(outputFile, 'speed_bin_centers', 'Dimensions', {'speed_bin', n_bins}, 'Datatype', 'double');
nccreate(outputFile, 'mean_speed', 'Dimensions', {'point', n_pts}, 'Datatype', 'single');
nccreate(outputFile, 'max_speed',  'Dimensions', {'point', n_pts}, 'Datatype', 'single');

ncwrite(outputFile, 'latitude',   lat);
ncwrite(outputFile, 'longitude',  lon);
ncwrite(outputFile, 'depth',      depth);
ncwrite(outputFile, 'speed_histogram', histograms);
ncwrite(outputFile, 'speed_bin_edges',   edges);
ncwrite(outputFile, 'speed_bin_centers', bin_centers);
ncwrite(outputFile, 'mean_speed', single(mean_speeds));
ncwrite(outputFile, 'max_speed',  single(max_speeds));

ncwriteatt(outputFile, 'latitude',        'units', 'degrees_north');
ncwriteatt(outputFile, 'longitude',       'units', 'degrees_east');
ncwriteatt(outputFile, 'depth',           'units', 'm');
ncwriteatt(outputFile, 'speed_histogram', 'units', 'probability');
ncwriteatt(outputFile, 'speed_bin_edges', 'units', 'm/s');
ncwriteatt(outputFile, 'speed_bin_centers', 'units', 'm/s');
ncwriteatt(outputFile, 'mean_speed',      'units', 'm/s');
ncwriteatt(outputFile, 'max_speed',       'units', 'm/s');

ncwriteatt(outputFile, '/', 'title', 'Tidal current speed histograms — US East Coast');
ncwriteatt(outputFile, '/', 'source', 'T_TIDE t_predic from ROMS harmonics (Pawlowicz et al., 2002)');
ncwriteatt(outputFile, '/', 'reconstruction_year', '2013');
ncwriteatt(outputFile, '/', 'time_step_hours', int32(1));
ncwriteatt(outputFile, '/', 'n_time_steps', int32(n_times));
ncwriteatt(outputFile, '/', 'n_points', int32(n_pts));
ncwriteatt(outputFile, '/', 'n_skipped', int32(n_skipped));
ncwriteatt(outputFile, '/', 'constituents', strjoin(valid_names, ', '));
ncwriteatt(outputFile, '/', 'histogram_bins', sprintf('%d bins, 0-5 m/s, 0.05 m/s step', n_bins));
ncwriteatt(outputFile, '/', 'created', datestr(now, 'yyyy-mm-ddTHH:MM:SS'));

file_info = dir(outputFile);
fprintf('Saved: %.1f MB\n', file_info.bytes / 1e6);
fprintf('Total time: %.1f hours\n', elapsed / 3600);
