%% Ground-truth reconstruction at one site using t_predic
% Reads harmonics from results/vp/groups/pooled/harmonics.nc
% Writes complex velocity timeseries to parity_matlab.mat next to this script.

scriptDir = fileparts(mfilename('fullpath'));
if isempty(scriptDir), scriptDir = pwd; end
repo = fullfile(scriptDir, '..', '..');

addpath(fullfile(repo, 'optimization', 'vp', 't_tide'));

harmonicsFile = fullfile(repo, 'results', 'vp', 'groups', 'pooled', 'harmonics.nc');
cmaj = ncread(harmonicsFile, 'current_semimajor');
cmin = ncread(harmonicsFile, 'current_semiminor');
cinc = ncread(harmonicsFile, 'current_inclination');
cpha = ncread(harmonicsFile, 'current_phase');
lat  = ncread(harmonicsFile, 'latitude');

% Match build_histograms.m: only transpose if leading dim is 10
if size(cmaj, 1) == 10
    cmaj = cmaj'; cmin = cmin'; cinc = cinc'; cpha = cpha';
end
fprintf('cmaj shape after conditional transpose: [%d %d]\n', size(cmaj, 1), size(cmaj, 2));

% Skip P1 (index 3) — same as the pipeline
valid_idx = [1, 2, 4, 5, 6, 7, 8, 9, 10];
valid_names = {'Q1', 'O1', 'K1', 'N2', 'M2', 'S2', 'K2', 'M4', 'M6'};
n_con = length(valid_names);

ipt = 1;  % point 0 (MATLAB 1-based) — change to probe another site
major = cmaj(ipt, valid_idx)';
minor = cmin(ipt, valid_idx)';
inc   = cinc(ipt, valid_idx)';
pha   = cpha(ipt, valid_idx)';

% Match constituents to T_TIDE
const = t_getconsts;
name_input = char(zeros(n_con, 4));
f = zeros(n_con, 1);
for k = 1:n_con
    idx = strmatch(valid_names{k}, const.name);
    name_input(k, :) = const.name(idx, :);
    f(k) = const.freq(idx);
end

% 2013 hourly time vector — same as the pipeline
tmin = datenum(2013, 1, 1, 0, 0, 0);
tmax = datenum(2013, 12, 31, 23, 0, 0);
t = (tmin : 1/24 : tmax)';

zer = zeros(n_con, 1);
tidecon_v = [major, zer, minor, zer, inc, zer, pha, zer];
v_pred = t_predic(t, name_input, f, tidecon_v, 'latitude', lat(ipt));

fprintf('len(v_pred) = %d, isreal = %d\n', length(v_pred), isreal(v_pred));
fprintf('first 5: '); disp(v_pred(1:5).');
fprintf('|v|: min=%.6f mean=%.6f max=%.6f\n', min(abs(v_pred)), mean(abs(v_pred)), max(abs(v_pred)));

outFile = fullfile(scriptDir, 'parity_matlab.mat');
save(outFile, 'v_pred', 't', 'lat', 'ipt', 'major', 'minor', 'inc', 'pha', 'f', 'valid_names', '-v7');
fprintf('Saved %s\n', outFile);
