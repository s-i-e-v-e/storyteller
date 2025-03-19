import re
from dataclasses import dataclass, field
from typing import List, NoReturn, Union, Optional

@dataclass
class Token:
    type: str
    value: str

@dataclass
class Context:
    scenes: List['Scene']
    xs: List[Union['User', 'Assistant']]

@dataclass
class Assistant:
    value: str

@dataclass
class User:
    xs: List[Union['UseScene', str]]

@dataclass
class Scene:
    value: str

@dataclass
class UseScene:
    value: int

def render_file(filepath: str) -> str:
    """
Reads the file, recursively includes other files, and returns the combined text.
    """
    try:
        with open(filepath, "r") as f:
            text = f.read()
            text = "\\context\n"+text+"\\end"
    except FileNotFoundError:
        raise_error(f"File not found: {filepath}")

    while True:
        match = re.search(r"^\\include\s+(.+)$", text, re.MULTILINE)
        if not match:
            break

        include_path = match.group(1).strip()
        try:
            with open(include_path, "r") as include_file:
                include_content = include_file.read()
        except FileNotFoundError:
            raise_error(f"Included file not found: {include_path}")

        text = text.replace(match.group(0), include_content, 1)

    while True:
        n = text.find('\\*')
        if n < 0:
            break
        nn = text.find('*\\', n)
        text = text[0: n] + text[nn+2:]

    idx = text.index('\\end')
    text = text[0: idx]
    text = text.strip()
    return text


def lex(text: str) -> list[Token]:
    """Lexes the input text into a list of Token objects."""

    tokens: List[Token] = []
    keywords = ['\\context\n', '\\user\n', '\\assistant\n', '\\scene\n', '\\use-scene', '\\characters']

    def add_str_token(x: str):
        if len(tokens) and tokens[-1].type == "STRING":
            tokens[-1].value += x
        else:
            tokens.append(Token(type='STRING', value=text[i]))

    i = 0
    while i < len(text):
        matched_keyword = None
        for keyword in keywords:
            if text[i:].startswith(keyword):
                matched_keyword = keyword
                break

        if matched_keyword:
            tokens.append(Token(type='KEYWORD', value=matched_keyword))
            i += len(matched_keyword)
        else:
            add_str_token(text[i])
            i += 1

    for t in tokens:
        t.value = t.value.strip()
    return tokens


def parse(tokens: List[Token]) -> List[Context]:
    """Parses a list of tokens into a list of Context objects."""

    contexts: List[Context] = []
    i = 0
    while i < len(tokens):
        if tokens[i].type == 'KEYWORD' and tokens[i].value == '\\context':
            context, i = parse_context(tokens, i + 1)
            contexts.append(context)
        else:
            raise_error("\\context block not found")
            i += 1  # Skip unexpected tokens
    return contexts


def parse_context(tokens: List[Token], start_index: int) -> tuple[Context, int]:
    """Parses a context block from the token stream."""

    scenes = []
    xs: List[Union[User, Assistant]] = []
    i = start_index
    while i < len(tokens):
        if tokens[i].type == 'KEYWORD' and tokens[i].value == '\\user':
            x, i = parse_user(tokens, scenes, i + 1)
            xs.append(x)
        elif tokens[i].type == 'KEYWORD' and tokens[i].value == '\\assistant':
            x, i = parse_assistant(tokens, i + 1)
            xs.append(x)
        elif tokens[i].type == 'KEYWORD' and tokens[i].value == '\\context':
            break # End current context
        elif tokens[i].type == 'STRING' and tokens[i].value == '':
            i += 1
        else:
            raise_error("Context can only contain \\include <filename> statements, and \\user & \\assistant blocks")
            i += 1
    return Context(scenes, xs), i


def parse_user(tokens: List[Token], scenes: list[Scene], start_index: int) -> tuple[User, int]:
    """Parses a user block from the token stream."""

    xs: List[Union[UseScene, str]] = []
    i = start_index
    while i < len(tokens):
        if tokens[i].type == 'KEYWORD' and tokens[i].value == '\\scene':
            x, i = parse_scene(tokens, i + 1)
            scenes.append(x)
        elif tokens[i].type == 'KEYWORD' and tokens[i].value == '\\use-scene':
            x, i = parse_use_scene(tokens, i + 1)
            xs.append(x)
        elif tokens[i].type == 'KEYWORD' and tokens[i].value == '\\characters':
            i += 1
        elif tokens[i].type == 'STRING':
            xs.append(tokens[i].value)
            i += 1
        elif tokens[i].type == 'KEYWORD' and (tokens[i].value == '\\user' or tokens[i].value == '\\assistant' or tokens[i].value == '\\context'):
            break  # End current user block
        else:
            break # End current user block
    return User(xs), i


def parse_assistant(tokens: List[Token], start_index: int) -> tuple[Assistant, int]:
    """Parses an agent block from the token stream."""
    xs = []
    i = start_index
    while i < len(tokens):
        if tokens[i].type == 'STRING':
            xs.append(tokens[i].value)
            i += 1
        else:
            break # End current user block
    return Assistant("".join(xs)), i


def parse_scene(tokens: List[Token], start_index: int) -> tuple[Scene, int]:
    """Parses a scene block from the token stream."""

    if start_index < len(tokens) and tokens[start_index].type == 'STRING':
        return Scene(tokens[start_index].value), start_index + 1
    else:
        return Scene(""), start_index # Empty Scene block

def parse_use_scene(tokens: List[Token], start_index: int) -> tuple[UseScene, int]:
    """Parses a use-scene statement from the token stream."""

    if start_index < len(tokens) and tokens[start_index].type == 'STRING':
        try:
            y = tokens[start_index].value+"\n"
            idx = y.find('\n')
            number = int(y[0:idx])
            tokens[start_index].value = y[idx:]
            return UseScene(number), start_index
        except ValueError:
            raise_error("Expected syntax: \\use-scene <number>")
    else:
        raise_error("Expected syntax: \\use-scene <number>")

def parse_file(filepath: str) -> list[Context]:
    """
Parses a file and returns a list of Context objects.
    """
    tokens = lex(render_file(filepath))
    return parse(tokens)

def raise_error(x: str) -> NoReturn:
    print(x)
    import sys
    sys.exit(-1)
