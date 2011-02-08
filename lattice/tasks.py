import modules
import os, sys, multiprocessing
import settings
import shutil
import pdlibs
import topo_sort, parmap

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
    props = filter(lambda x : _is_derived_out_of_date(x, x.replace(src_dir, settings.class_output)), props)
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
            
    cmd = 'javac -g -encoding utf-8  %s -d %s %s' % (classpath, class_output,  ' '.join(java_srcs))
    if options.verbose:
        print cmd

    if not options.dry_run:
        ok = os.system(cmd)
        if ok != 0:
            print ' ##### Failed to compile module %s ' % mod
            sys.exit(ok)


    
def build(mod,  *args, **dict_p):
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

def run(module, main_class, *args, **dict_p):
    # ensure module has already been compiled
    build(module)
    print 'Running Java class %s in module %s\n' % (main_class, module)
    classpath = modules.get_class_path_for_mod(module) 
    # assume any named args are JVM options
    java = 'java '
    if len(dict_p) > 0:
        for (key, val) in dict_p.items():
            if key == 'extra_class_path':
                classpath = classpath + ':' + val
            elif key == 'run_libs' : # extra run time only libraries
                for lib in val.split(','):
                    classpath = classpath + ':' + ':'.join(pdlibs.lib_jar_files[lib])
            else:
                java = java + ('-X' + key) + val + ' ' 
    cmd = java  + ' -cp ' + classpath + " "  + main_class + ' ' + ' '.join(args)
    print cmd
    ok = os.system(cmd)
    if ok != 0:
        print ' ##### Failed to run class %s for module %s, have you built the module first? ' % (main_class, module)
        sys.exit(ok)

def gwt_compile(job):
    """
    web_module: where the GWT compile output should go into
    gwt_src_module: where is the GWT source code
    """
    (web_module, (gwt_src_module, entry_class), dict_p) = job
    cores = 1 # parallelize not at browser permutation level, but GWT module level
    jvm_mem = '500m'
    gwt_style = 'OBF'
    if len(dict_p) > 0:
        for (key, val) in dict_p.items():
            if key == 'mx':
                jvm_mem = val
            elif key == 'style':
                gwt_style = val
                
    run(gwt_src_module,  'com.google.gwt.dev.Compiler', '-style ' + gwt_style, '-war ' + settings.war_dir(web_module) + os.sep + 'gwt -localWorkers ' + str(cores), entry_class, mx=jvm_mem, extra_class_path=settings.src_dir(gwt_src_module) )


def build_gwts(module_name, *args, **dict_p):
    """
    module_name: the web module which should define list of gwt modules in  its build file
    """
    build(module_name)
    module = modules.mod_name_mapping[module_name]
    if hasattr(module, 'gwt_modules'):
        cores = multiprocessing.cpu_count()
        params = [ (module_name, gwt_mod, dict_p) for gwt_mod in module.gwt_modules]
        parmap.parmap(gwt_compile, cores, params)
    

def jar(module,  *args, **dict_p):
    _compile(module)
    print 'Creating %s.jar in %s/%s' % (module, module, settings.jar_output)
    cls_dir = settings.class_dir(module)
    if not os.path.exists(cls_dir):
        print '##### No classes found in module build directory %s, unable to create jar. Maybe you need to run the build task ("-t build") first? ' % settings.class_dir(module)
        #sys.exit(1)
        return
    
    if not os.path.exists(settings.jar_dir(module)):
        os.makedirs(settings.jar_dir(module))

    jar_file = '%s/%s.jar' % (settings.jar_dir(module), module)  

    cmd = 'jar cf %s -C %s .' % (jar_file, cls_dir) 
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
    
    
def clean(module, *args, **dict_p):
    _transitive_op_core(clean_local, module, [])


def junit(module, main_class, *args, **dict_p):
    # assume module has already been compiled
    print 'Not implemented Running test %s in module %s\n' % (main_class, module)
    # TODO where to put junit.jar?


def war_jars(module, web_root_dir=settings.web_root):
    """
    build all jars of dependent modules and copy to buid/war/WEB-INF/lib
    """
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

    web_inf_lib_dir =  settings.war_dir(module) + os.path.sep + 'WEB-INF' + os.path.sep + 'lib'
    if not os.path.isdir(web_inf_lib_dir):
        os.makedirs(web_inf_lib_dir)

    print '----- Prepare jars in the war file '
    print 'These jars will be copied into the WEB-INF/lib directory :', web_inf_jars
    for jar_file in web_inf_jars:
        shutil.copyfile(jar_file, web_inf_lib_dir + os.path.sep + os.path.basename(jar_file))



def war_web_content(module, web_root_dir=settings.web_root):
    """
    web_root_dir: root folder of the web files (HTML JSP etc)
    Will prepare all files in the war staging dir, including the jars , short of zip up the final .war file
    """
    # verify web root
    web_root = module + os.path.sep + web_root_dir
    
    # create the staging directory for WAR
    war_staging_dir = settings.war_dir(module)
    if os.path.exists(war_staging_dir):
        print ' ---- deleting staging dir %s' % war_staging_dir
        shutil.rmtree(war_staging_dir)
    # copy all jars to WEB-INF/lib
    print '----- Copy all files under %s to staging dir %s ' % (web_root , war_staging_dir)
    shutil.copytree(web_root, war_staging_dir)
    # copy the web inf jars
    war_jars(module, web_root_dir)

def pack_war(module,  web_root_dir=settings.web_root):
    war_file = module + os.path.sep + settings.war_output + os.path.sep + module + '.war'
    war_staging_dir = settings.war_dir(module)
    cmd = 'jar cf %s -C %s .' % (war_file, war_staging_dir)
    print cmd
    ok = os.system(cmd)
    if ok != 0:
        print ' ##### Failed to package jar file for module %s ' % (module)
        sys.exit(ok)
    else:
        print ' ----- Successfully built %s ' % war_file



def war(module, web_root_dir=settings.web_root):
    """
    create a war file where all the dependent module and library jars are put under WEB-INF/lib

    web_root root folder of the web files (HTML JSP etc)
    """
    war_web_content(module, web_root_dir)
    pack_war(module, web_root_dir)


def gwt_war(module, *args, **dict_p):
    """
    """
    war_web_content(module)
    build_gwts(module, args,dict_p)
    pack_war(module)
