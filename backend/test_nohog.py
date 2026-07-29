import os, sys, time
sys.path.insert(0, '/app')
from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS
from collections import Counter

c = PhotoClassifier()
t0 = time.time()

per_pos = {}
for folder in sorted(os.listdir('/app/fotos_prueba')):
    fpath = os.path.join('/app/fotos_prueba', folder)
    if not os.path.isdir(fpath):
        continue
    expected = int(folder.split(' -')[0])
    correct = 0
    total = 0
    for img in sorted(os.listdir(fpath)):
        path = os.path.join(fpath, img)
        if not os.path.isfile(path):
            continue
        pos, info = c.classify(path)
        total += 1
        if pos == expected:
            correct += 1
        else:
            label = INSPECTION_POSITIONS.get(pos, 'N/A') if pos else 'N/A'
            print('  FAIL %s -> %s (%s, %s)' % (folder, label, info.get('method','?'), info.get('confidence','?')))
    per_pos[expected] = (correct, total)

print()
for pos in sorted(per_pos):
    c, t = per_pos[pos]
    print('Pos %2d (%s): %d/%d (%d%%)' % (pos, INSPECTION_POSITIONS[pos], c, t, c*100//t))
print()
total_c = sum(v[0] for v in per_pos.values())
total_t = sum(v[1] for v in per_pos.values())
print('Total: %d/%d (%.1f%%)' % (total_c, total_t, total_c*100.0/total_t))
print('Elapsed: %.1fs' % (time.time() - t0))
