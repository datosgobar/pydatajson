from multiprocessing.pool import ThreadPool


def apply_threading(l, function, cant_threads):
    pool = ThreadPool(processes=cant_threads)

    return pool.map(function, l)
