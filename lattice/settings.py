import os

java_src = 'src/main/java'
class_output = 'build/classes'
test_class_output = 'build/testclasses'
jar_output = 'target'
war_output = 'target'
test_src = 'src/test/java'
resource_src ='src/main/resources'
web_root = 'src/main/web'
war_tmp_folder = 'build/war'
lib_path = 'lib'
dirs_to_clean = ['target', 'build', 'ecl_classes']

def src_dir(module):
    return module + os.sep + java_src

def test_src_dir(module):
    return module + os.sep + test_src

def class_dir(module):
    return module + os.sep + class_output

def test_class_dir(module):
    return module + os.sep + test_class_output

def war_dir(module):
    return module + os.sep + war_tmp_folder

def jar_dir(module):
    return module + os.sep + jar_output

def clean_dirs(module):
    return map(lambda x : module + os.sep + x , dirs_to_clean)
