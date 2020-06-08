def chunks(data, size=30):
    """ Split iterable thing into n-sized chunks """
    for i in range(0, len(data), size):
        yield data[i : i + size]
