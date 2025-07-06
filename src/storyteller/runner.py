import fs
from parser import Node, parse


def consume(n: Node, output_len: int, messages: list[str], output: str):
    output = output.strip()

    if n.do_summarize:
        xs = "\n\\summary\n"
        xs += output
        fs.append_text(n.summary_file, xs)
    else:
        xs = "\n\\assistant\n"
        xs += output
        fs.append_text(n.output_file, xs)

        fs.append_text("main.md", f"\n\\assistant {output_len}\n")


def use(file: str, model: str, c):
    import llm

    m = c.models[model]
    messages, n, output_len = parse(file)
    content = llm.query(m, messages)
    consume(n, output_len, messages, content)


def render(file: str):
    xs = []
    messages, _ = parse(file)
    for x in messages:
        xs.append("\\" + x["role"])
        xs.append("\n")
        xs.append(x["content"])
        xs.append("\n")
        xs.append("\n")

    print("".join(xs))
