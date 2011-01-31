import multiprocessing


def _pickle_method(method):
    func_name = method.im_func.__name__
    obj = method.im_self
    cls = method.im_class
    return _unpickle_method, (func_name, obj, cls)

def _unpickle_method(func_name, obj, cls):
    for cls in cls.mro():
        try:
            func = cls.__dict__[func_name]
        except KeyError:
            pass
        else:
            break
        
    res = func.__get__(obj, cls)
    return res
    

import copy_reg
import types
copy_reg.pickle(types.MethodType, _pickle_method, _unpickle_method)

def parmap(func, num_processes, args):
    """
    Parallel map
    Arguments:
       num_processes, how many processes to launch
       others: see Python map doc
    
    Return:
       same as a regular Python map function
    
    """
    
    if num_processes == 1:
        return map(func, args)
    elif num_processes  > 1 :
        pool = multiprocessing.Pool(num_processes)
        return pool.map(func, args)
    else:
        raise 'Invalid processes arg ' + str(num_processes)




if __name__ == '__main__':
    def add8(num):
        return num + 8


    class Adder(object):
        def __init__(self, how_many = 1):
            self.how_many = how_many

        def __str__(self):
            return "Adder adding " + str(self.how_many)


        def add(self, num):
            return self.how_many + num
    
    args =  range(10)

    result = parmap(add8, 2, args)
    print result

    adder = Adder(8)
    args = list(range(10))
    result = parmap(adder.add, 4, args)
    print result

    
