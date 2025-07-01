from dataclasses import dataclass
from typing import cast

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
class DefineSummary:
    file: str


@dataclass
class DefineScene:
    file: str


@dataclass
class DefineLog:
    file: str


@dataclass
class DefineOutput:
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
class System:
    val: str


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
    summary: str
    scene: str
    output: str
    log: str
    summary_prompt: str
    do_reset: bool
    summarize: bool
    xs: list[Main | User | Reset]


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
    return xs


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
    return xs


def __parse_define(
    cs: CharStream,
) -> DefineSummary | DefineScene | DefineOutput | DefineLog:
    cs.skip_ws()
    id = __parse_id(cs)
    cs.skip_ws()
    start = cs.i
    file = __parse_file_name(cs)
    if id == "summary":
        return DefineSummary(file)
    elif id == "scene":
        return DefineScene(file)
    elif id == "output":
        return DefineOutput(file)
    elif id == "log":
        return DefineLog(file)
    elif id == "summarize":
        cs.rewind(start)
        return DefineSummaryPrompt(__parse_prompt(cs))
    else:
        raise Exception(f"Unknown definition {id}")


def __parse_system(cs: CharStream) -> System:
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
    return System(xs)


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
                elif id == "reset":
                    n.xs.append(Reset(0))
                elif id == "summarize":
                    n.xs.append(Summarize(0))
                else:
                    cs.rewind(start)
                    break
        else:
            xs += cs.next()
    if xs:
        n.xs.append(xs)
    return n


def __parse_user(cs: CharStream) -> User:
    x = __parse_main(cs)
    return User(x.xs)


def __parse_user_commands(n: Node):
    scene = fs.read_text(n.scene).split("\scene")
    summary = fs.read_text(n.summary).split("\summary")

    for x in n.xs:
        is_last = x == n.xs[-1]
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
                elif type(y) is Reset and is_last:
                    n.do_reset = True
                elif type(y) is Summarize and is_last:
                    n.summarize = True
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
    log = fs.read_text(n.log) if fs.exists(n.log) else ""
    if not log:
        ys = [x for x in n.xs if type(x) is Main]
        for y in ys:
            log += "\\user\n"
            log += "".join(y.xs).strip()
            log += "\n"

    a = n.xs[-1]
    assert type(a) is User or type(a) is Main
    z = cast(User, a)

    log += "\\user\n"
    log += "".join(z.xs).strip()
    log += "\n"

    if n.summarize:
        log += n.summary_prompt
        log += "\n"

    USER = "user\n"
    ASSISTANT = "assistant\n"
    messages = []
    for x in (
        log.replace("\n\n", "\n")
        .replace("\\user", "\\$user")
        .replace("\\assistant", "\\$assistant")
        .split("\\$")
    ):
        x = x.strip()
        if x.startswith(USER):
            messages.append({"role": "user", "content": x[len(USER) :]})
        elif x.startswith(ASSISTANT):
            messages.append({"role": "assistant", "content": x[len(ASSISTANT) :]})
        elif not x:
            pass
        else:
            raise Exception
    return messages, n


def __loop(cs: CharStream) -> Node:
    n = Node(
        "root",
        "summary.md",
        "scene.md",
        "output.md",
        "chat.log",
        "# SUMMARIZE\nSummarize the contents of the context",
        False,
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
                if type(q) is DefineScene:
                    n.scene = q.file
                elif type(q) is DefineSummary:
                    n.summary = q.file
                elif type(q) is DefineOutput:
                    n.output = q.file
                elif type(q) is DefineLog:
                    n.log = q.file
                elif type(q) is DefineSummaryPrompt:
                    n.summary_prompt = q.val
                else:
                    raise Exception
            elif id == "system":
                n.xs.append(__parse_system(cs))
            elif id == "main":
                n.xs.append(__parse_main(cs))
            elif id == "user":
                n.xs.append(__parse_user(cs))
            else:
                raise Exception(f"Unknown instruction {id}")
        else:
            raise Exception(f"Expected: \define \\user \main \\reset: {cs.xx[cs.i :]}")

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
