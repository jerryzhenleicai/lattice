import os, sys
import pdlibs
import topo_sort
import settings

# a hash map mapping from module name to its  Python module object
mod_name_mapping = dict() 

mod_dep_relations = dict()

# map from a module name to a list of modules it transitively depends on
mod_dep_mods = dict()

# map from a module name to a list of libraries it transitively depends on
mod_dep_libs = dict()

def find_direct_dependencies(mod):
    module = __import__(mod)
    deps = []
    if  hasattr(module, 'depends') :
        if isinstance(module.depends, list):
            deps = module.depends
        else:
            deps = [module.depends]
    return deps


def find_all_mods():
    """
    search all immediate subdirectories of current working dir and treat any directory with a
    __init__.py file as a module (skip the lib directory)
    """
    cwd  = os.getcwd()
    subdirs =  [name for name in os.listdir(cwd) if os.path.isdir(os.path.join(cwd, name))]
    subdirs = filter(lambda x : x != settings.lib_path , subdirs)
    subdirs = filter(lambda x : os.path.exists(cwd + os.sep + x + os.sep + '__init__.py') , subdirs)
    return subdirs

def collect_dependencies(top_mod):
    """
    Given a module, recursively find all the modules and libraries it depends on (transitively)
    
    return a 3 tuple (relations,mod_set,lib_set) where:

    relations is a list of two tuples (A,B), where A and B are modules and A depends on B
    mod_set: will be filled with all the modules top_mod depends on
    lib_set: will be filled with all libraries top_mod depends on 
    """
    # already computed?
    if mod_dep_mods.has_key(top_mod):
        return (mod_dep_relations[top_mod], mod_dep_mods[top_mod], mod_dep_libs[top_mod])
    
    module = __import__(top_mod)
    mod_name_mapping[top_mod] = module
    deps = find_direct_dependencies(top_mod)
    dep_relations = [ (top_mod,x ) for x in deps ]
    mod_set = set()
    lib_set = set()
    if hasattr(module, 'libs'):
        lib_set |= set(module.libs)
    
    # recursively add
    for dep in deps:
        if not dep in mod_set: # deal with cycles and a module appear a dependency twice 
            sub_relations, sub_mods, sub_libs = collect_dependencies(dep)
            dep_relations += sub_relations
            mod_set |= sub_mods
            lib_set |= sub_libs
        mod_set.add(dep)
        
    mod_dep_mods[top_mod] = mod_set
    mod_dep_libs[top_mod] = lib_set
    mod_dep_relations[top_mod] = dep_relations
    return dep_relations, mod_set, lib_set


def get_class_path_for_mod(mod, jar_only = False):
    """
    Build the class path needed for running module 
    """
    class_output = mod + os.sep + settings.class_output
    collect_dependencies(mod)
    dep_libs = mod_dep_libs[mod]
    
    if len(dep_libs) == 0:
        classpath = ""
    else:
        jar_files = []
        for lib in dep_libs:
            jar_files += pdlibs.lib_jar_files[lib]
            
        classpath = (":".join(jar_files))

    # expand class path to dependent modules, so their classes instead of sources will be used for type info during compile
    for dep in list(mod_dep_mods[mod]) +  [mod]:
        if jar_only:
            classpath = classpath + ':' + dep + os.sep + settings.jar_output + os.sep + dep + '.jar'
        else:
            classpath = classpath + ':' + dep + os.sep + settings.class_output
    return classpath
       
            
