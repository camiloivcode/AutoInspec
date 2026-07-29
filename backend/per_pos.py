import os, sys
sys.path.insert(0, '/app')
from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS
from collections import Counter

c = PhotoClassifier()
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
    per_pos[expected] = (correct, total)

for pos in sorted(per_pos):
    c, t = per_pos[pos]
    print('Pos %2d (%s): %d/%d (%d%%)' % (pos, INSPECTION_POSITIONS[pos], c, t, c*100//t))
