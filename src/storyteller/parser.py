import re
from dataclasses import dataclass, field
from typing import List, Union, Optional

@dataclass
class Scene:
    text: str

@dataclass
class UseScene:
    id: int

@dataclass
class Context:
    xs: List[Union[str, UseScene]] = field(default_factory=list)
    scenes: List[Scene] = field(default_factory=list)

@dataclass
class ParseContext:
    xs: List[Union[str, Context]] = field(default_factory=list)

@dataclass
class Token:
    type: str  # "KEYWORD" or "STRING"
    value: str

def render_file(filepath: str) -> str:
    """
Reads the file, recursively includes other files, and returns the combined text.
    """
    try:
        with open(filepath, "r") as f:
            text = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")

    while True:
        match = re.search(r"^\\include\s+(.+)$", text, re.MULTILINE)
        if not match:
            break

        include_path = match.group(1).strip()
        try:
            with open(include_path, "r") as include_file:
                include_content = include_file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Included file not found: {include_path}")

        text = text.replace(match.group(0), include_content, 1)
    idx = text.index('\\end')
    text = text[0: idx]
    return text

@dataclass
class TokenStream:
    tokens: List[Token]
    pos: int = 0

    def next(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return None

    def peek(self) -> Optional[Token]:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type: str) -> Token:
        token = self.next()
        if token is None or token.type != expected_type:
            raise ValueError(f"Expected {expected_type}, but got {token}")
        return token

class Lexer:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.text = render_file(filepath)
        self.pos = 0
        self.text_len = len(self.text)

    def lex(self) -> TokenStream:
        tokens = []
        while self.pos < self.text_len:
            if self.text[self.pos] == '\\':
                # Keyword
                match = re.match(r"\\(\w[\w-]*)", self.text[self.pos:])  # Allow hyphens in keyword names
                if match:
                    keyword = match.group(0)  # Include the backslash
                    tokens.append(Token("KEYWORD", keyword))
                    self.pos += len(keyword)
                else:
                    # Invalid keyword
                    raise ValueError(f"Invalid keyword at position {self.pos}")
            else:
                # String
                match = re.match(r"([^\\]+)", self.text[self.pos:]) #Match everything that doesn't start with backslash.
                if match:
                    string = match.group(0)
                    tokens.append(Token("STRING", string))
                    self.pos += len(string)
                else:
                    self.pos += 1
        return TokenStream(tokens)

class Parser:
    def __init__(self, token_stream: TokenStream):
        self.token_stream = token_stream

    def parse(self) -> ParseContext:
        """
Parses the token stream and returns a ParseContext object.
        """
        parse_context = ParseContext()

        while self.token_stream.peek() is not None:
            token = self.token_stream.peek()
            if token.type == "KEYWORD" and token.value == "\\context":
                self.token_stream.next()  # Consume "\\context"
                context = self._parse_context()
                parse_context.xs.append(context)
            elif token.type == "KEYWORD" and token.value == "\\prompt":
                self.token_stream.next()  # Consume "\\prompt"
                string = self.token_stream.next().value
                parse_context.xs[-1].xs.append(string.strip())
            elif token.type == "STRING":
                string = self.token_stream.next().value
                parse_context.xs[-1].xs.append(string.strip())
            else:
                raise ValueError(f"Unexpected token: {token}")
        return parse_context

    def _parse_context(self) -> Context:
        """
Parses a context block.
        """
        context = Context()
        while self.token_stream.peek() is not None:
            token = self.token_stream.peek()

            if token.type == "KEYWORD":
                if token.value == "\\scene":
                    self.token_stream.next()  # Consume "\\scene"
                    scene = self._parse_scene()
                    context.scenes.append(scene)
                elif token.value == "\\use-scene":
                    self.token_stream.next()  # Consume "\\use-scene"
                    use_scene = self._parse_use_scene()
                    context.xs.append(use_scene)
                else:
                    break  # End of context block
            elif token.type == "STRING":
                string = self.token_stream.next().value
                context.xs.append(string.strip())
            else:
                break # End of context.

        return context

    def _parse_scene(self) -> Scene:
        """
Parses a scene block.
        """
        text = ""
        while True:
            token = self.token_stream.peek()
            if token is None or token.type != "STRING":
                break

            text += self.token_stream.next().value

        return Scene(text.strip())

    def _parse_use_scene(self) -> UseScene:
        """
Parses a use-scene block.
        """
        token = self.token_stream.consume("STRING")
        match = re.match(r"#(\d+)", token.value.strip())
        if match:
            scene_id = int(match.group(1))
            return UseScene(id=scene_id)
        else:
            raise ValueError("Expected scene ID after \\use-scene")

def parse_file(filepath: str) -> ParseContext:
    """
Parses a file and returns a ParseContext object.
    """
    lexer = Lexer(filepath)
    token_stream = lexer.lex()
    parser = Parser(token_stream)
    return parser.parse()
