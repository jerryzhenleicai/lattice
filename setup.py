from setuptools import setup, find_packages

setup(name='lattice',
      version='0.9',
      description='Java Build tool in Python',
      author='Zhenlei Cai',
      author_email='jpenguin@gmail.com',
      url='http://www.python.org/sigs/distutils-sig/',
      include_package_data = True,
      packages=['lattice'],
      package_data = {
        '': ['*.jar'],
       }
     )

