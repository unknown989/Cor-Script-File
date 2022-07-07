from .exception import raise_excp


def call_func(name, args):

    try:
        exec(f"{name}({','.join(args)})")
    except:
        raise_excp(
            f"function with name '{name}' doesn't exist, or the args '[{','.join(args)}]' do not match")


def call_func_with_return(name, args):
    try:
        return eval(f"{name}({','.join(args)})")
    except NameError:
        raise_excp(
            f"function with name '{name}' doesn't exist, or the args '[{','.join(args)}]' do not match")


def add_nums(a, b):
    return f"Hello There {str(a+b)}"


def strip(string, pattern):
    return string.replace(string, pattern)
