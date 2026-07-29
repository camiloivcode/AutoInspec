import os
for folder in sorted(os.listdir('/app/fotos_prueba')):
    fpath = os.path.join('/app/fotos_prueba', folder)
    if os.path.isdir(fpath):
        n = len([f for f in os.listdir(fpath) if os.path.isfile(os.path.join(fpath, f))])
        print('  %s: %d files' % (folder, n))
