from multiprocessing.pool import ThreadPool


def apply_threading(l, function, cant_threads):
    pool = ThreadPool(processes=cant_threads)
    results = pool.map(function, l)
    pool.close()
    pool.join()
    return results
