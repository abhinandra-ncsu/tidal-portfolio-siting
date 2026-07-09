%% View one site — reconstruct speed timeseries + histogram (Stage 1)
%
% Sanity check that T_TIDE produces a physical tidal current before
% committing to the full-population run (build_histograms.m). Reconstructs a
% single site and plots speed(t) next to its 0-5 m/s @ 0.05 histogram.
%
% Default site = strongest M2 semi-major (most energetic). Set SITE below to
% inspect a specific point index instead.
%
% Input: results/harmonics.nc   (from 01_extract_harmonics.py)

clear; close all; clc;

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir), scriptDir = pwd; end
repoRoot = fileparts(fileparts(scriptDir));
vpDir = fullfile(repoRoot, 'optimization', 'vp');
addpath(fullfile(vpDir, 'config'));
if ~exist('t_predic', 'file'), addpath(fullfile(vpDir, 't_tide')); end

cfg = config();
edges = 0.0 : 0.05 : 5.0;
bin_centers = edges(1:end-1) + 0.025;
t = (cfg.tmin : cfg.dt : cfg.tmax)';

%% Read harmonics
inputFile = fullfile(scriptDir, 'results', 'harmonics.nc');
cmaj = ncread(inputFile, 'current_semimajor');   % (constituent x point)
cmin = ncread(inputFile, 'current_semiminor');
cinc = ncread(inputFile, 'current_inclination');
cpha = ncread(inputFile, 'current_phase');
lat  = ncread(inputFile, 'latitude');
lon  = ncread(inputFile, 'longitude');
depth = ncread(inputFile, 'depth');

if size(cmaj, 1) == 10
    cmaj = cmaj'; cmin = cmin'; cinc = cinc'; cpha = cpha';   % -> (point x constituent)
end

%% Pick the site
M2_COL = 6;   % constituent order: q1 o1 p1 k1 n2 m2 s2 k2 m4 m6
[~, SITE] = max(cmaj(:, M2_COL));   % strongest M2 site
% SITE = 12345;   % uncomment to inspect a specific point index

%% Reconstruct that one site (mirrors build_histograms.m)
valid_idx = cfg.valid_idx; valid_names = cfg.valid_names; n_con = numel(valid_names);
major = cmaj(SITE, valid_idx)'; minor = cmin(SITE, valid_idx)';
inc   = cinc(SITE, valid_idx)'; pha   = cpha(SITE, valid_idx)';
major(isnan(major)) = 0; minor(isnan(minor)) = 0; inc(isnan(inc)) = 0; pha(isnan(pha)) = 0;

const = t_getconsts;
name_input = char(zeros(n_con, 4)); f = zeros(n_con, 1);
for k = 1:n_con
    idx = strmatch(valid_names{k}, const.name);
    name_input(k, :) = const.name(idx, :); f(k) = const.freq(idx);
end

zer = zeros(n_con, 1);
tidecon_v = [major, zer, minor, zer, inc, zer, pha, zer];
v_pred = t_predic(t, name_input, f, tidecon_v, 'latitude', lat(SITE));
speed = abs(v_pred);

fprintf('Site %d: lat %.4f, lon %.4f, depth %.1f m\n', SITE, lat(SITE), lon(SITE), depth(SITE));
fprintf('  mean %.3f m/s, max %.3f m/s\n', mean(speed), max(speed));

%% Plot
figure('Position', [100 100 900 700]);

subplot(2, 1, 1);
plot(t, speed, 'LineWidth', 0.4); datetick('x', 'mmm'); grid on;
ylabel('speed |W|  (m/s)'); xlabel('2013');
title(sprintf('Site %d  (%.3f N, %.3f W, %.0f m) — speed(t)', ...
      SITE, lat(SITE), -lon(SITE), depth(SITE)));

subplot(2, 1, 2);
h = histcounts(speed, edges, 'Normalization', 'probability');
bar(bin_centers, h, 1.0, 'EdgeColor', 'none'); grid on;
xlabel('speed |W|  (m/s)'); ylabel('probability');
xlim([0 max(0.5, max(speed) * 1.1)]);
title('per-site speed histogram (0-5 m/s @ 0.05)');
