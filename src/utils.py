def empty_to_none(arg):
    if not arg:
        return None
    else:
        return arg


def ceval(arg):
    try:
        return eval(arg)
    except (NameError, SyntaxError):
        return empty_to_none(arg)
