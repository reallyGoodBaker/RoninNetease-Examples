def remove(list, item):
    # type: (list, object) -> bool
    try:
        list.remove(item)
        return True
    except ValueError:
        return False

def chunk(list, size):
    # type: (list, int) -> list
    return [list[i:i + size] for i in range(0, len(list), size)]

def flatten(list):
    # type: (list) -> list
    return [item for sublist in list for item in sublist]

def compact(list):
    # type: (list) -> list
    return [item for item in list if item]

def fill(list, item, start=0, end=None): # type: ignore
    # type: (list, object, int, int) -> list
    if end is None:
        end = len(list)
    list[start:end] = [item] * (end - start)
    return list

def without(list, item):
    # type: (list, object) -> list
    return [x for x in list if x != item]