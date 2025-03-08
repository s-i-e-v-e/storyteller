def fix_demented_path_resolution(mod: str):
    import sys
    import os
    for i in range(len(sys.path)):
        if sys.path[i].endswith(f'{os.sep}src{os.sep}{mod}'):
            sys.path[i] = os.sep.join(sys.path[i].split(os.sep)[:-1])

def load_context(file: str):
    from parser import parse_file, User, Assistant, UseScene

    messages = []
    xs = parse_file(file)
    c =  xs[-1]

    messages.append({"role": "assistant", "content": "I am a helpful AI assistant. My goal is to help you in any way you want without judgment."})
    for x in c.xs:
        if isinstance(x, User):
            zs = []
            for y in x.xs:
                if isinstance(y, str):
                    zs.append(y)
                elif isinstance(y, UseScene):
                    zs.append('\n')
                    zs.append(c.scenes[y.value-1].value)
                else:
                    raise Exception
            messages.append({"role": "user", "content": "\n".join(zs)})
        elif isinstance(x, Assistant):
            messages.append({"role": "assistant", "content": x.value})
        else:
            raise Exception
    return messages

def use(model: str, file: str):
    import config, llm, fs

    c = config.load()
    m = c.models[model]
    messages = load_context(file)
    content = llm.query(m, messages)
    fs.append_text(file, '\n\n\\assistant\n'+content)

def render(file: str):
    xs = []
    xs.append('\\context')
    xs.append('\n')
    messages = load_context(file)
    for x in messages:
        xs.append('\\'+x['role'])
        xs.append('\n')
        xs.append(x['content'])
        xs.append('\n')
        xs.append('\n')

    print("".join(xs))

def print_help():
    """Prints the command-line interface (CLI) help"""
    print("storyteller: A tool for writing stories")
    print("\nCommands:")
    print("  use <model> <path-to-file>  - Use a specified language model to process a given file.")
    print("                              <model>: The name of the LLM/service to use (e.g., 'koboldcpp', 'llamacpp'). Refer to the storyteller.toml file.")
    print("                              <path-to-file>: The path to the file you want to process.")
    print("  render <path-to-file>      - Render the given file  in the terminal after resolving all imports.")
    print("                              <path-to-file>: The path to the file to render.")

def main():
    import sys
    fix_demented_path_resolution('storyteller')
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    match sys.argv[1]:
        case 'use': use(sys.argv[2], sys.argv[3])
        case 'render': render(sys.argv[2])
        case _:
            print("Unknown command: "+sys.argv[1])
            help()

main()
