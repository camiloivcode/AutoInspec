import os, sys, time, shutil, json
sys.path.insert(0, '/app')

ref_dir = '/app/ref_train'
for d in [ref_dir]:
    if os.path.exists(d):
        shutil.rmtree(d)

holdout_paths = []
for folder in sorted(os.listdir('/app/fotos_prueba')):
    src = os.path.join('/app/fotos_prueba', folder)
    if not os.path.isdir(src):
        continue
    images = sorted(os.listdir(src))
    if len(images) < 2:
        continue
    dst = os.path.join(ref_dir, folder)
    os.makedirs(dst, exist_ok=True)
    holdout_img = images[-1]
    for img in images[:-1]:
        shutil.copy2(os.path.join(src, img), os.path.join(dst, img))
    holdout_paths.append((folder, os.path.join(src, holdout_img)))

from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS
from src.infrastructure.analysis.reference_matcher import extract_features

c = PhotoClassifier(ref_dir)
t0 = time.time()

correct = 0
total = 0
for folder, path in holdout_paths:
    expected_pos = int(folder.split(' -')[0])
    
    features = extract_features(path)
    if features:
        if c.matcher.centroids:
            best_pos = None; best_dist = float('inf'); second_best = float('inf')
            for pos, cent in c.matcher.centroids.items():
                dist = c.matcher._distance_to_centroid(features, cent)
                if dist < best_dist:
                    second_best = best_dist; best_dist = dist; best_pos = pos
                elif dist < second_best:
                    second_best = dist
            margin = (second_best - best_dist) / (best_dist + 1e-6) if best_pos else 0
            print('  %s -> best=%d(dist=%.3f), 2nd=%d(dist=%.3f), margin=%.3f' % (
                folder, best_pos, best_dist, 
                second_best if second_best < float('inf') else 0,
                second_best if second_best < float('inf') else 0,
                margin))
    
    pos, info = c.classify(path)
    total += 1
    label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
    status = 'OK' if pos == expected_pos else 'FAIL'
    if pos == expected_pos:
        correct += 1
    print('  >>> %s %s -> %s (%s, %s)' % (status, folder, label, info.get('method','?'), info.get('confidence','?')))
    print()

print('Elapsed: %.1fs' % (time.time() - t0))
print('Total: %d/%d correct (%d%%)' % (correct, total, correct*100//total if total > 0 else 0))
