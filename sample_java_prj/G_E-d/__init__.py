from lattice import tasks

depends = [ 'E_a-b-c', 'd']

libs = ['logging', 'commons']


def run_main(mod, threads = 4, points=5) :
    print threads, points
    tasks.run(__name__, 'org.lattice.G', ' '.join([str(threads), str(points)]), mx='1024m'  )
