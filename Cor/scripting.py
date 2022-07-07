from .Utils.exception import raise_excp, print_warn
from csf_config import Config

from .Utils import scripting_functions as csf_defs

import enum
import re


variables_in_scope = list()


def get_var_from_scope(var_name, line):
    verificator = LangTypesVerification()

    for v in variables_in_scope:
        if v["name"] == var_name:
            return v
    return None


def get_var_type(var, line):
    if re.search(r"^\"[^/]*\"$", var):
        return VarTypes.String
    elif re.search(r"[0-9]+", var):
        return VarTypes.Int
    elif re.search(r"^(true)$|^(false)$", var):
        return VarTypes.Bool
    elif re.search(r"^[a-zA-Z]+\([^/]*?\)$", var):
        return VarTypes.Function
    else:
        if Config.ALLOW_UNKNOWN_TYPES:
            print_warn(f"statement '{var}' at line {line} is of unknown type")
            return VarTypes.Unknown
        else:
            raise_excp(f"statement '{var}' at line {line} is of unknown type")


class LangTypes(enum.Enum):
    def __init__(self):
        Var = 1  # $
        DefinedFunc = 2  # func
        Comment = 3  # //
        Plus = 4  # +
        Minus = 5  # -
        Multiplty = 6  # *
        Divise = 7  # /
        Equal = 8  # =
        Text = 9  # a-zA-Z...
        Number = 10  # 0-9


class LangTypesVerification:
    def __init__(self):
        self.var = r"^\$[a-zA-Z0-9]+\s?=\s?([a-zA-Z0-9]|(,|.|'|\"|\?))+"
        self.number = r"^[0-9]+$"
        self.text = r"^\"([a-zA-Z0-9]|,|.|'|\"|\?)+\"$"
        self.func = r"^[a-zA-Z\S]+\((([a-zA-Z]+)?,?)[^/]*\)$"
        self.comment = r"^\/\/.*"

    def get_all_types(self):
        v = [(_, self.__getattribute__(_)) for _ in dir(self) if not _.startswith(
            "_") and not callable(getattr(self, _))]
        return v

    def verify(self, val, line):
        if re.search(r"^(\n+)?(\t+)?$", val):
            return
        for (t, v) in self.get_all_types():
            if(re.search(v, val)):
                return {"statement": val, "type": t, "line": line}
        raise_excp(
            f"statement '{val}' at line {line} is of unknown/invalid syntax")


class VarTypes(enum.Enum):
    Int = 1
    String = 2
    Bool = 3
    Function = 4
    Unknown = 5


class Scanner:
    def __init__(self, buffer):
        self.buffer = buffer

    def scan(self):
        new_buffer = self.buffer.split("\n")  # separator is a space
        for line, buf in enumerate(new_buffer):
            yield LangTypesVerification().verify(buf, line+1)


class StandaloneParsers:
    def __init__(self):
        pass

    def parse_var(stmt: str, line):
        nstmt = stmt.split("=")
        variables_in_scope.append(
            {"name": nstmt[0].strip(), "value": nstmt[1].strip()})

        var_name = nstmt[0][1:].strip()
        var_val = nstmt[1].strip()
        var_type = get_var_type(var_val, line)
        if var_type == VarTypes.Function:
            func_parse = StandaloneParsers.parse_func(var_val, line)
            var_val = Runtime.run_func(func_parse)
        if var_type == VarTypes.String:
            var_val = var_val[1:len(var_val)-1]

        return {"variable_name": var_name, "variable_value": var_val, "variable_type": var_type}

    def parse_func(stmt: str, line):
        name = re.findall(r"^[^0-9(,|.|'|\"|\?|\$)]+\(", stmt)
        return_out = {"name": "", "args": []}
        # Handling Function Name
        if not len(name) == 1:
            raise_excp(
                f"statement '{stmt}' at line {line} is of unknown syntax, functions must not have punctuations, numbers and spaces on them")
        else:
            return_out["name"] = name[0].replace("(", "")
        # Handling Function Args (whooo)
        args = stmt.replace(return_out["name"], "").replace(
            "(", "").replace(")", "")
        args = args.split(",")

        arg_stack = list()

        for arg in args:
            arg_dict = {"arg_value": "",
                        "arg_type": ""}
            if arg.startswith("$"):  # Dealing with variables
                var_from_scope = get_var_from_scope(arg.strip(), line)
                if var_from_scope is None:
                    raise_excp(
                        f"argument '{arg}' in statement '{stmt}' at line {line} is not defined")
                arg_dict["arg_value"] = var_from_scope["value"]
                arg_dict["arg_type"] = get_var_type(
                    var_from_scope["value"], line)
                arg_stack.append(arg_dict)
            else:
                var_type = get_var_type(arg, line)
                arg_dict["arg_type"] = var_type
                arg_dict["arg_value"] = arg
                arg_stack.append(arg_dict)
        return_out["args"] = arg_stack
        return return_out


class Runtime:
    def __init__(self, scope_stack):
        self.scope = scope_stack

    def run(self):
        for instruction in self.scope:
            if instruction.get("variable_name"):
                continue

            def_to_call = instruction["name"]
            def_args = [v["arg_value"] for v in instruction["args"]]

            csf_defs.call_func(def_to_call, def_args)

    def run_func(func_obj):
        func_to_call = func_obj["name"]
        func_args = [v["arg_value"] for v in func_obj["args"]]
        return csf_defs.call_func_with_return(func_to_call, func_args)


def parser(filename):
    buffer = open(filename, "r").read()
    scan = list(Scanner(buffer).scan())

    scope_stack = list()
    for stmt in scan:
        if not stmt:
            continue
        if stmt["type"] == "var":
            scope_stack.append(StandaloneParsers.parse_var(
                stmt["statement"], stmt["line"]))
        if stmt["type"] == "func":
            scope_stack.append(StandaloneParsers.parse_func(
                stmt["statement"], stmt["line"]))
        if stmt["type"] == "number":
            print_warn("statement "+stmt["statement"] +
                       " at line "+str(stmt["line"])+" has no effect")
        if stmt["type"] == "text":
            print_warn("statement "+stmt["statement"] +
                       " at line "+str(stmt["line"])+" has no effect")
        if stmt["type"] == "comment":
            continue  # Skip the statement with a comment

    runtime = Runtime(scope_stack)
    runtime.run()

    return scope_stack

# TODO: implement the runtime
