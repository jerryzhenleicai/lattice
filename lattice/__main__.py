import shutil
import optparse, os, sys
import eclipse, settings
import modules, pdlibs
import tasks
from modules import  collect_dependencies, find_all_mods
import inspect
    

def run_task(module_name, task, named_args):
    """
    Run a task for a module

    First search in the module definition file for the task name, if found then execute the task according to the task definition, otherwise search the built-in system tasks in tasks.py

    Parameter module name of the module
    """
    module = __import__(module_name)
    
    if hasattr(module, task):
        task_method = getattr(module, task)
        task_method(module_name)
    elif hasattr(tasks, task):
        task_method = getattr(tasks, task)
        if not named_args is None:
            print 'Running task %s on module %s ' % (task, module_name) + ' with args ' + str(named_args)
            task_method(module_name,  **named_args)
        else:
            task_method(module_name)
    else:
        raise Exception('neither module %s nor system tasks has task %s defined' %  (module_name, task))

def expand_mods():
    """
    """
    pass

def print_settings():
    print 'To change any of the settings, create a custom settings.py file to replace the one installed. The current settings are:'
    print 'Java source: \t\t %s' % settings.java_src
    print 'Resource files:\t\t %s' % settings.resource_src 
    print 'Web files root:\t\t %s' % settings.web_root
    print 'Library jars :\t\t %s' % settings.lib_path
    print 'Class output during compile:\t %s' % settings.class_output
    print 'Directory to output .jar\'s :\t\t %s' % settings.jar_output 
    print 'Directory to output .war\'s :\t\t %s' % settings.war_output 
    
    
def gen_eclipse_prjs(dry_run, verbose):
    # do all libraries
    for lib in pdlibs.lib_jars_short:
        eclipse.gen_lib(lib, dry_run, verbose)
    # generate the bulk import plugin file, see http://code.nomad-labs.com/eclipse-bulk-import/
    bulkprj = open('./projectList.txt', 'w')
    lib_top = os.getcwd() + os.sep + settings.lib_path
    for lib in sorted(pdlibs.lib_jars_short):
        bulkprj.write(lib_top + os.sep + lib + '\n')
    # do all modules
    for mod in sorted(find_all_mods()):
        if verbose:
            print mod
        dummy, dep_mods, libs = collect_dependencies(mod)
        eclipse.gen_module(mod, dep_mods, libs, dry_run, verbose)
        bulkprj.write(os.getcwd() + os.sep + mod + '\n')
    bulkprj.close()


def listfunc(me):
    for name in dir(me):
        obj = getattr(me, name)
        if inspect.isfunction(obj):
            yield name
            
if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('-m', '--module')
    p.add_option('-T', '--disable-transitive-dependencies', action='store_true', help='by default when a module is built all of its dependent modules are built first, this flag will disable this behavior')
    p.add_option('-s', '--show-settings', help='List build settings such as default source and target directories', action='store_true')
    p.add_option('-D', '--show-dependencies', action='store_true')
    p.add_option('-v', '--verbose', action='store_true')
    p.add_option('-d', '--debug', action='store_true')
    p.add_option('-r', '--dry-run', action='store_true')
    p.add_option('-L', '--list-libs', action='store_true')
    p.add_option('-p', '--parallel-compiles', default='4')
    p.add_option('-e', '--eclipse-gen', action='store_true', help="generate eclipse project files for all modules and libraries")
    candidate_tasks = filter(lambda x : not x.startswith('_') ,  list(listfunc(tasks)))
    p.add_option('-t', '--run-task', default='build', help='one of: ' + '|'.join(candidate_tasks) )
    p.add_option('-a', '--task-args', help='arguments to the task')
    
    options,arguments = p.parse_args()
    if options.show_settings:
        print_settings()
        sys.exit(0)
    
    if options.debug:
        options.verbose = True

    mod = options.module
    
    # scan the jars in lib directory 
    pdlibs.build_jar_lib(options.list_libs)

    if options.eclipse_gen:
        gen_eclipse_prjs(options.dry_run, options.verbose)
        sys.exit(0)
    elif not mod:
        print 'You must use the --module option to specify the module'
        all_mods = find_all_mods()
        if len(all_mods) > 0:
            print 'These are the modules found in the current directory: %s.' % ",".join(all_mods)
        p.print_help()
        sys.exit(1)
        
    if mod[-1] == os.path.sep:
        mod = mod[:-1]
        
    if options.show_dependencies:
        dummy, deps, libs = collect_dependencies(mod)
        print 'Listing dependencies of module %s: ' % mod
        print 'Modules it depends on (including indirect ones): %s.' % ','.join(deps)
        print 'Libraries it depends on (including indirect ones): %s.' % ','.join(libs)
    elif not options.run_task is None:
        tasks.options = options
        args = dict()
        if not options.task_args is None:
            argclauses = options.task_args.split(',')
            for clause in argclauses:
                (key, val) = clause.split('=')
                args[key] = val
        run_task(mod, options.run_task, args)
    else :
        p.print_help()
    
