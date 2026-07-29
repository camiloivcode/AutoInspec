import os, sys
sys.path.insert(0, '/app')
from src.infrastructure.analysis.reference_matcher import extract_features, _chi2_dist
import numpy as np

base = '/app/fotos_prueba'

all_features = {}
for folder in sorted(os.listdir(base)):
    fpath = os.path.join(base, folder)
    if not os.path.isdir(fpath):
        continue
    pos = int(folder.split(' -')[0])
    for fname in sorted(os.listdir(fpath)):
        path = os.path.join(fpath, fname)
        if not os.path.isfile(path): continue
        feats = extract_features(path)
        if feats:
            all_features.setdefault(pos, []).append(feats)

for pos in sorted(all_features.keys()):
    feats = all_features[pos]
    centroid = {}
    for k in ['brightness','color_std','edge_pct','sat_mean','hue_mean','blue_ratio','green_ratio','laplacian_var','center_brightness','center_std']:
        centroid[k] = np.mean([f[k] for f in feats])
    print('Pos %2d: b=%5.0f cs=%5.0f ep=%5.1f%% sat=%5.0f hue=%5.0f bl=%4.2f gr=%4.2f lap=%5.0f cb=%5.0f cst=%5.0f  (n=%d)' % (
        pos, centroid['brightness'], centroid['color_std'], centroid['edge_pct'],
        centroid['sat_mean'], centroid['hue_mean'], centroid['blue_ratio'],
        centroid['green_ratio'], centroid['laplacian_var'],
        centroid['center_brightness'], centroid['center_std'],
        len(feats)))
