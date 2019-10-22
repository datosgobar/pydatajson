# -*- coding: utf-8 -*-

from multiprocessing.pool import ThreadPool


def apply_threading(l, function, cant_threads, **kwargs):
    if cant_threads == 1:
        return [function(x, **kwargs) for x in l]
    pool = ThreadPool(processes=cant_threads)
    results = pool.map(function, l)
    pool.close()
    pool.join()
    return results
