from dataclasses import dataclass
from typing import Type, cast

import fs


@dataclass
class CharStream:
    i: int
    max: int
    xx: str

    def __init__(self, xx: str):
        self.xx = xx
        self.i = 0
        self.max = len(xx)

    def error(self, m: str, idx: int):
        idx = idx if idx else self.i
        line = 1 + self.xx.count("\n", 0, idx)
        a = self.xx.rfind("\n", 0, idx)
        b = self.xx.find("\n", idx)
        char = idx - a
        x = self.xx[idx:b]
        return Exception(f"{m}: {x} (L{line}C{char})")

    def eos(self):
        return self.i >= self.max

    def peek(self):
        if self.eos():
            return ""
        return self.xx[self.i]

    def next(self):
        if self.eos():
            return ""
        x = self.xx[self.i]
        self.i += 1
        return x

    def skip_ws(self):
        while self.peek() in " \t\n":
            self.next()

    def rewind(self, i: int):
        self.i = i


@dataclass
class DefineSummaryFile:
    file: str


@dataclass
class DefineSceneFile:
    file: str


@dataclass
class DefineLogFile:
    file: str


@dataclass
class DefineOutputFile:
    file: str


@dataclass
class DefineSummaryPrompt:
    val: str


@dataclass
class Include:
    file: str


@dataclass
class IncludeScene:
    number: int


@dataclass
class IncludeSummary:
    number: int


@dataclass
class Assistant:
    number: int
    xs: list["Include|IncludeScene|IncludeSummary|str"]


@dataclass
class Main:
    xs: list["Include|IncludeScene|IncludeSummary|str"]


@dataclass
class User:
    xs: list["Include|IncludeScene|IncludeSummary|str"]


@dataclass
class Reset:
    dummy: int


@dataclass
class Summarize:
    dummy: int


@dataclass
class Node:
    id: str
    summary_file: str
    scene_file: str
    output_file: str
    log_file: str
    summary_prompt: str
    do_summarize: bool
    xs: list[Main | User | Assistant]


def __parse_atom(cs: CharStream, first: str, next: str):
    start = cs.i

    xs = ""
    if cs.peek() not in first:
        raise cs.error("invalid ID", start)

    xs += cs.next()

    while not cs.eos():
        if cs.peek() in next:
            xs += cs.next()
        else:
            break
    return xs.strip()


def __parse_file_name(cs: CharStream):
    FIRST = "abcdefghijklmnopqrstuvwyxz0123456789-/_."
    NEXT = FIRST
    return __parse_atom(cs, FIRST, NEXT)


def __parse_id(cs: CharStream):
    FIRST = "abcdefghijklmnopqrstuvwyxz"
    NEXT = FIRST + "0123456789-"
    return __parse_atom(cs, FIRST, NEXT)


def __parse_number(cs: CharStream) -> int:
    FIRST = "0123456789"
    NEXT = FIRST
    return int(__parse_atom(cs, FIRST, NEXT))


def __parse_include(
    cs: CharStream,
) -> Include | IncludeSummary | IncludeScene:
    cs.skip_ws()
    file_or_id = __parse_file_name(cs)
    if file_or_id == "summary":
        cs.skip_ws()
        num = __parse_number(cs)
        return IncludeSummary(num)
    elif file_or_id == "scene":
        cs.skip_ws()
        num = __parse_number(cs)
        return IncludeScene(num)
    else:
        file = file_or_id
        return Include(file)


def __parse_prompt(cs: CharStream):
    xs = ""
    while not cs.eos():
        x = cs.peek()
        if x == "\n":
            break
        else:
            xs += cs.next()
    return xs.strip()


def __parse_define(
    cs: CharStream,
) -> DefineSummaryFile | DefineSceneFile | DefineOutputFile | DefineLogFile:
    cs.skip_ws()
    id = __parse_id(cs)
    if id == "file":
        cs.skip_ws()
        id = __parse_id(cs)
        cs.skip_ws()
        file = __parse_file_name(cs)
        if id == "summary":
            return DefineSummaryFile(file)
        elif id == "scene":
            return DefineSceneFile(file)
        elif id == "output":
            return DefineOutputFile(file)
        elif id == "log":
            return DefineLogFile(file)
        else:
            raise Exception(f"Unknown definition {id}")
    elif id == "prompt":
        cs.skip_ws()
        id = __parse_id(cs)
        cs.skip_ws()
        if id == "summary":
            return DefineSummaryPrompt(__parse_prompt(cs))
        else:
            raise Exception(f"Unknown definition {id}")
    else:
        raise Exception(f"Unknown definition {id}")


def __parse_assistant(cs: CharStream) -> Assistant:
    xs = ""
    while not cs.eos():
        start = cs.i
        x = cs.peek()
        if x == "\\":
            cs.next()
            if cs.peek() == "\\":
                xs += cs.next()
            else:
                cs.rewind(start)
                break

        else:
            xs += cs.next()
    return Assistant(-1, [xs.strip()])


def __parse_main(cs: CharStream) -> Main:
    n = Main([])
    xs = ""
    while not cs.eos():
        start = cs.i
        x = cs.peek()
        if x == "\\":
            cs.next()
            if cs.peek() == "\\":
                xs += cs.next()
            else:
                id = __parse_id(cs)
                if id == "include":
                    n.xs.append(xs)
                    xs = ""
                    n.xs.append(__parse_include(cs))
                else:
                    cs.rewind(start)
                    break
        else:
            xs += cs.next()
    xs = xs.strip()
    if xs:
        n.xs.append(xs)
    return n


def __parse_user(cs: CharStream) -> User:
    x = __parse_main(cs)
    return User(x.xs)


def __parse_user_commands(n: Node):
    scene = fs.try_read_text(n.scene_file).split("\scene")
    summary = fs.try_read_text(n.summary_file).split("\summary")

    for x in n.xs:
        ty = type(x)
        if ty is Main or ty is User:
            ys = []
            for y in x.xs:
                if type(y) is IncludeScene:
                    z = cast(IncludeScene, y)
                    ys.append(scene[z.number])
                elif type(y) is IncludeSummary:
                    z = cast(IncludeSummary, y)
                    ys.append(summary[z.number])
                else:
                    ys.append(y)
            x.xs.clear()
            x.xs.extend(ys)


def __parse_file_includes(n: Node):
    for x in n.xs:
        ty = type(x)
        if ty is Main or ty is User:
            ys = []
            for y in x.xs:
                if type(y) is Include:
                    z = cast(Include, y)
                    cs = __as_stream(z.file)
                    p = __parse_main(cs)
                    assert cs.eos()
                    ys.extend(p.xs)
                else:
                    ys.append(y)
            x.xs.clear()
            x.xs.extend(ys)


def __build_messages(n: Node) -> list[str]:
    def get_text(ty: Type, x: any):
        return "".join(cast(ty, x).xs).strip()

    def handle_reset():
        n.xs.reverse()
        try:
            j = n.xs.index(Reset(0))
        except ValueError:
            j = -1
        if j >= 0:
            n.xs = n.xs[0:j]
        n.xs.reverse()

    handle_reset()

    output = fs.try_read_text(n.output_file).split("\\assistant")[1:]

    messages = []
    for x in n.xs:
        ty_x = type(x)
        if ty_x is User:
            y = get_text(User, x)
            messages.append({"role": "user", "content": y})
        elif ty_x is Main:
            y = get_text(User, x)
            messages.append({"role": "user", "content": y})
        elif ty_x is Assistant:
            x = cast(Assistant, x)
            if x.number >= 0:
                y = output[x.number]
            else:
                y = get_text(Assistant, x)
            messages.append({"role": "assistant", "content": y})
        elif ty_x is Summarize:
            n.do_summarize = True
        else:
            print(type(x))
            raise Exception

        if ty_x is not Summarize:
            # a \user \assistant block supercedes these commands
            n.do_summarize = False

    if n.do_summarize:
        assert n.summary_prompt.strip()
        messages.append({"role": "user", "content": n.summary_prompt})
    return messages, n, len(output)


def __loop(cs: CharStream) -> Node:
    n = Node(
        "root",
        "summary.md",
        "scene.md",
        "output.md",
        "chat.log",
        "",
        False,
        [],
    )
    while not cs.eos():
        cs.skip_ws()
        x = cs.peek()
        if x == "\\":
            cs.next()
            id = __parse_id(cs)
            if id == "define":
                q = __parse_define(cs)
                if type(q) is DefineSceneFile:
                    n.scene_file = q.file
                elif type(q) is DefineSummaryFile:
                    n.summary_file = q.file
                elif type(q) is DefineOutputFile:
                    n.output_file = q.file
                elif type(q) is DefineSummaryPrompt:
                    n.summary_prompt = q.val
                else:
                    raise Exception
            elif id == "main":
                n.xs.append(__parse_main(cs))
            elif id == "user":
                n.xs.append(__parse_user(cs))
            elif id == "assistant":
                cs.skip_ws()
                num = __parse_number(cs)
                n.xs.append(Assistant(num, []))
            elif id == "fakeassistant":
                n.xs.append(__parse_assistant(cs))
            elif id == "reset":
                n.xs.append(Reset(0))
            elif id == "summarize":
                n.xs.append(Summarize(0))
            else:
                raise Exception(f"Unknown instruction {id}")
        else:
            raise Exception(
                f"Expected: \define \\user \main \\fakeassistant \summarize \\reset: {cs.xx[cs.i :]}"
            )

    __parse_file_includes(n)

    return n


def __as_stream(path: str) -> CharStream:
    source = fs.read_text(path)
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    return CharStream(source)


def parse(path: str) -> list[str]:
    n = __loop(__as_stream(path))
    __parse_user_commands(n)
    return __build_messages(n)
