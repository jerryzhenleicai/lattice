import modules
import os, sys
import settings
import shutil
import topo_sort

options = None

def _transitive_op_core(op, module, excludes):
    """
    Remove all non-source dirs
    """
    if module in excludes:
        return
    op(module)
    excludes.append(module)
    
    # recursive transitive_op all dep modules
    map(lambda x : _transitive_op_core(op, x, excludes), modules.find_direct_dependencies(module))

def _get_srcs_below_dir(dir, ext = None):
    srcs = []
    for root, dirs, files in os.walk(dir):
        srcs = srcs + map(lambda y : root + '/' + y, filter(lambda x : ext is None or x.endswith(ext), files))
    return srcs

def _is_derived_out_of_date(src, derived):
    if not os.path.exists(derived):
        return True
    src_time = os.stat(src).st_mtime
    derived_time = os.stat(derived).st_mtime
    return src_time > derived_time

def _is_class_out_of_date(src):
    class_file = src.replace(settings.java_src, settings.class_output).replace('.java', '.class')
    return _is_derived_out_of_date(src,class_file)


def _compile(mod):
    module = modules.mod_name_mapping[mod]
    src_dir = (mod + os.sep + settings.java_src)
    resource_dir = mod + os.sep + settings.resource_src
    class_output = settings.class_dir(mod)

    if not os.path.exists(class_output):
        os.makedirs(class_output)

    # copy resources files such as .properties
    if os.path.exists(resource_dir):
        # if there are out-of-date resource files in build target dir, clean buld dir and copy all resources
        # to the build directory. This is to simplify the build logic
        rsrcs = _get_srcs_below_dir(resource_dir)
        rsrcs = filter(lambda x : _is_derived_out_of_date(x, x.replace(settings.resource_src, settings.class_output)), rsrcs)
        if len(rsrcs) > 0:
            print 'Resource files out of date, deleting all in %s and rebulding' % class_output
            # delete target class dir if any
            if os.path.exists(class_output):
                shutil.rmtree(class_output)
            shutil.copytree(resource_dir, class_output)
    
    classpath = modules.get_class_path_for_mod(mod)
    if len(classpath) > 0 :
        classpath = '-cp ' + classpath

    # if there are properties and XML config files in src, copy them to classes
    props = _get_srcs_below_dir(src_dir, '.properties') + _get_srcs_below_dir(src_dir, '.xml')
    if len(props) > 0:
        for prop in props:
            path = prop[len(src_dir):]
            dest = class_output + path
            if options.verbose:
                print 'Copying to ' + dest
            # check dir exists
            dest_dir = dest[:dest.rfind(os.sep)]
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copyfile(prop, dest)

    java_srcs = _get_srcs_below_dir(src_dir, '.java')
    java_srcs = filter(  _is_class_out_of_date, java_srcs)
    if len(java_srcs) == 0:
        print '------------------- \n No Java source code in %s need to be recompiled since they are all up-to-date' % mod
        return
        
    # compile .java's that are obsolete wrt their corresponding .class files
    print '--------------------- \n Compiling %s ' % mod
            
    cmd = 'javac -encoding utf-8  %s -d %s %s' % (classpath, class_output,  ' '.join(java_srcs))
    if options.verbose:
        max_cmp_len = 1000 
        if len(cmd) < max_cmp_len or options.debug:
            print cmd
        else:
            print cmd[:max_cmp_len/2] + ' ... ' + cmd[-max_cmp_len/2:]

    if not options.dry_run:
        ok = os.system(cmd)
        if ok != 0:
            print ' ##### Failed to compile module %s ' % mod
            sys.exit(ok)


    
def build(mod):
    """
    Compile a module, recursively compile all other modules this module depends on first in the correct order
    """
    dep_relations, all_mods, dummy = modules.collect_dependencies(mod)
    all_mods.add(mod)
    if not options.disable_transitive_dependencies:
        sorted_mods = topo_sort.topological_sort(all_mods, dep_relations)
        if isinstance(sorted_mods, tuple):
            loop = sorted_mods[1]
            raise Exception('Sorry a circular dependency is found in modules, the loop : %s ' %   "->".join(loop))
        sorted_mods.reverse()
        
        if options.verbose:
            print '+----------------------- Building %s ----------------------------------------------------- ' % mod
            print '| all modules related to %s : %s' % (mod, ", ".join(sorted_mods))
            print '| pairwise dependencies : %s' %  ",  ".join( map(lambda (x,y) : x +" -> " + y,  dep_relations) )
        
    else:
        sorted_mods = [mod]
    if options.verbose:
        print '| compiling all modules in this order: ', sorted_mods
        print '+---------------------------------------------------------------------------------------------'

    # See which moduls can be built in parallel,
    map(_compile, sorted_mods)

def run_java_class(module, main_class, *args, **dict_p):
    # assume module has already been compiled
    print 'Running Java class %s in module %s\n' % (main_class, module)
    classpath = modules.get_class_path_for_mod(module)
    # assume any named args are JVM options
    java = 'java '
    if len(dict_p) > 0:
        for (key, val) in dict_p.items():
            java += ('-X' + key) +  val
    cmd = java  + ' -cp ' + classpath + " "  + main_class + ' ' + ' '.join(args)
    print cmd
    ok = os.system(cmd)
    if ok != 0:
        print ' ##### Failed to run class %s for module %s, have you built the module first? ' % (main_class, module)
        sys.exit(ok)


def jar(module):
    print 'Creating %s.jar in %s/%s' % (module, module, settings.jar_output)
    
    if not os.path.exists(settings.class_dir(module)):
        print '##### No classes found in module build directory %s, unable to create jar. Maybe you need to run the build task ("-t build") first? ' % settings.class_dir(module)
        #sys.exit(1)
        return
    
    if not os.path.exists(settings.jar_dir(module)):
        os.makedirs(settings.jar_dir(module))
        
    cmd = 'jar cf %s/%s.jar -C %s .' % (settings.jar_dir(module), module, settings.class_dir(module)) 
    print cmd
    ok = os.system(cmd)
    if ok != 0:
        print ' ##### Failed to package jar file for module %s ' % (module)
        sys.exit(ok)    


def jar_all(module):
    """
    Jar the module and all its dependent modules recursively
    """
    _transitive_op_core(jar, module, [])


def clean_local(module):
    print 'Clean all (classes , jars ...) under module %s' % module
    for cdir in settings.clean_dirs(module):
        if os.path.exists(cdir):
            shutil.rmtree(cdir)
    
    
def clean(module):
    _transitive_op_core(clean_local, module, [])


def junit(module, main_class, *args, **dict_p):
    # assume module has already been compiled
    print 'Not implemented Running test %s in module %s\n' % (main_class, module)
    # TODO where to put junit.jar?

def war(module, web_root_dir=settings.web_root):
    """
    create a war file where all the dependent module and library jars are put under WEB-INF/lib

    web_root root folder of the web files (HTML JSP etc)
    """
    # verify web root
    web_root = module + os.path.sep + web_root_dir
    if not os.path.isdir(web_root):
        print ' ####  The web root dir %s is not an existing directory ' % web_root
        return

    if not options.disable_transitive_dependencies:
        build(module)
        jar_all(module)
        
    # verify all dependent module/library jars have been built/exist
    all_jars = modules.get_class_path_for_mod(module, jar_only = True)
    web_inf_jars = all_jars.split(':')
    for jar_file in web_inf_jars:
        if not os.path.exists(jar_file):
            print "Jar file required for building WAR does not exist : %s, Rebuilding %s.jar and all its dependent module jars. " % (jar_file, module)
            jar_all(module)
            break
    
    
    # create the staging directory for WAR
    war_staging_dir = module + os.path.sep + settings.war_tmp_folder
    if os.path.exists(war_staging_dir):
        print ' ---- deleting staging dir %s' % war_staging_dir
        shutil.rmtree(war_staging_dir)
    # copy all jars to WEB-INF/lib
    print '----- Copy all files under %s to staging dir %s ' % (web_root , war_staging_dir)
    shutil.copytree(web_root, war_staging_dir)
    web_inf_lib_dir = war_staging_dir + os.path.sep + 'WEB-INF' + os.path.sep + 'lib'
    os.makedirs(web_inf_lib_dir)

    
    print '----- Prepare jars in the war file '
    for jar_file in web_inf_jars:
        shutil.copyfile(jar_file, web_inf_lib_dir + os.path.sep + os.path.basename(jar_file))

    
    print 'These jars will be copied into the WEB-INF/lib directory :', web_inf_jars
    war_file = module + os.path.sep + settings.war_output + os.path.sep + module + '.war'
    cmd = 'jar cf %s -C %s .' % (war_file, war_staging_dir)
    print cmd
    ok = os.system(cmd)
    if ok != 0:
        print ' ##### Failed to package jar file for module %s ' % (module)
        sys.exit(ok)
    else:
        print ' ----- Successfully built %s ' % war_file
    # delete staging dir ? 
    #shutil.rmtree(