from multiprocessing.pool import ThreadPool


def apply_threading(l, function, cant_threads):
    if cant_threads == 1:
        return [function(x) for x in l]
    pool = ThreadPool(processes=cant_threads)
    results = pool.map(function, l)
    pool.close()
    pool.join()
    return results
