import os

java_src = 'src/main/java'
class_output = 'build/classes'
jar_output = 'target'
war_output = 'target'
test_src = 'src/test/java'
resource_src ='src/main/resources'
web_root = 'src/main/web'
war_tmp_folder = 'build/war'
lib_path = 'lib'
dirs_to_clean = ['target', 'build', 'ecl_classes']

def class_dir(module):
    return module + os.sep + class_output

def jar_dir(module):
    return module + os.sep + jar_output

def clean_dirs(module):
    return map(lambda x : module + os.sep + x , dirs_to_clean)