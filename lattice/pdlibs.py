import os
import settings

prefix = len(settings.lib_path) + 1
lib_jars_short = dict() # mapping from library symbolic name to all jars it contains (short name)
lib_jar_files = dict() # mapping from library symbolic name to all jars it contains (full path)

def build_jar_lib(verbose):
    print 'Scanning for jars under %s ...' % settings.lib_path
    
    if verbose:
        print 'Third party libaries found'

    if not os.path.exists(settings.lib_path):
        print 'Warning: library folder %s not found, assuming no dependy on external library jars.'
        return
    
    for root in [os.path.join(settings.lib_path, name) for name in os.listdir(settings.lib_path) if os.path.isdir(os.path.join(settings.lib_path, name))]:
        files =  [name for name in os.listdir(root) if os.path.isfile(os.path.join(root, name))]
        root = root[prefix:]
        if root == '':
            continue
        paths = root.split('/')
        if len(paths) == 0:
            continue
        # ignore hidden directories
        if len(filter(lambda x : x[0] == '.' and len(x) > 1, paths)) > 0 :
            continue

        jars = filter(lambda x : x.endswith('.jar'), files)
        lib_jar_files[root] = map(lambda x : settings.lib_path + '/' + root + '/' + x , jars) # or use sys.modules[__name__] and setattr
        lib_jars_short[root] = jars
        if verbose:
            print '%s: \t %s' % (root, ",".join(jars))



