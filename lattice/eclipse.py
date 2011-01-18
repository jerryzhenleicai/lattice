# http://code.nomad-labs.com/eclipse-bulk-import/

import modules
import pdlibs
import settings

ecl_prj_types = {
    'java' :
"""<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
\t<name>%s</name>
\t<comment></comment>
\t<projects>
\t</projects>
\t<buildSpec>
\t\t<buildCommand>
\t\t\t<name>org.eclipse.jdt.core.javabuilder</name>
\t\t\t<arguments>
\t\t\t</arguments>
\t\t</buildCommand>
\t</buildSpec>
\t<natures>
\t\t<nature>org.eclipse.jdt.core.javanature</nature>
\t</natures>
</projectDescription>
""" ,  'javascript' :
    
"""<?xml version="1.0" encoding="UTF-8"?>
<projectDescription>
\t<name>%s</name>
\t<comment></comment>
\t<projects>
\t</projects>
\t<buildSpec>
\t\t<buildCommand>
\t\t\t<name>org.eclipse.wst.jsdt.core.javascriptValidator</name>
\t\t\t<arguments>
\t\t\t</arguments>
\t\t</buildCommand>
\t</buildSpec>
\t<natures>
\t\t<nature>org.eclipse.wst.jsdt.core.jsNature</nature>
\t</natures>
</projectDescription>
"""
    }

    

def gen_proj(mod, lib, module):
    """
    Write the .project file
    Return True if it's a Java or jar project 
    """
    if lib :
        fdir = settings.lib_path + '/' + mod
    else:
        fdir = mod
    prj = open(fdir + '/.project', 'w')
    etype = 'java'
    if module:
        if hasattr(module,'eclipse_type'):
            etype = module.eclipse_type
    prj.write(ecl_prj_types[etype] % mod)
    prj.close()
    return etype == 'java'
    
def gen_module(mod, dep_mods, dep_libs, dry_run = False, verbose = False):
    """
    Generate the eclipse .project and .classpath files for a module including transitive dependencies
    
    Input:
       dep_mods: modules this module directly or indirectly depends on
       dep_libs: libraries  this module directly or indirectly depends on
    """
    module = __import__(mod)
    # gen .classpath
    is_java = gen_proj(mod, False, module)
    if not is_java:
        return
    clspath = \
"""<?xml version="1.0" encoding="UTF-8"?>
<classpath>
\t<classpathentry kind="src" path="%s"/>
\t<classpathentry kind="con" path="org.eclipse.jdt.launching.JRE_CONTAINER"/>
""" % (settings.java_src)
    # add all dependent modules as Eclipse dependent projects
    for dep in sorted(dep_mods | dep_libs):
        clspath += '\n\t<classpathentry combineaccessrules="false" kind="src" path="/%s"/>' % dep
        
    # add 
    clspath += '\n\t<classpathentry kind="output" path="ecl_classes"/>'              
    clspath += "\n</classpath>\n"              
    cls = open(mod + '/.classpath', 'w')
    cls.write(clspath)
    cls.close()


def gen_lib(mod, dry_run = False, verbose = False):
    gen_proj(mod, True, None)
    clspath = \
"""<?xml version="1.0" encoding="UTF-8"?>
<classpath>
\t<classpathentry kind="con" path="org.eclipse.jdt.launching.JRE_CONTAINER"/>
"""
    # add all jars
    for jar in pdlibs.lib_jars_short[mod]:
        clspath += '\n\t<classpathentry exported="true" kind="lib" path="%s"/>' % jar
    clspath += "\n</classpath>\n"              
    cls = open(settings.lib_path + '/' + mod + '/.classpath', 'w')
    cls.write(clspath)
    cls.close()
 
