import fs
from parser import Node, parse


def consume(n: Node, messages: list[str], output: str):
    output = output.strip()

    if n.do_reset:
        fs.archive_file(n.output)
        fs.archive_file(n.log)

    if n.summarize:
        xs = ""
        xs += "\n\n"
        xs += "\\summary\n"
        xs += output
        fs.append_text(n.summary, xs)
    else:
        xs = ""
        xs += "\n\n"
        xs += "\\assistant\n"
        xs += output
        fs.append_text(n.output, xs)
        messages.append({"role": "assistant", "content": output})

        xs = ""
        for x in messages:
            xs += "\n"
            xs += "\\"
            xs += x["role"]
            xs += "\n"
            xs += x["content"]
        fs.write_text(n.log, xs)


def use(file: str, model: str, c):
    import llm

    m = c.models[model]
    messages, n = parse(file)
    content = llm.query(m, messages)
    consume(n, messages, content)


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
