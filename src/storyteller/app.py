def fix_demented_path_resolution(mod: str):
    import sys
    for i in range(len(sys.path)):
        if sys.path[i].endswith(f'/src/{mod}'):
            sys.path[i] = '/'.join(sys.path[i].split('/')[:-1])

def load_context(file: str):
    from storyteller.parser import parse_file, Context, UseScene

    parse_context = parse_file(file)
    ys = [x for x in parse_context.xs if isinstance(x, Context)]
    c =  ys[-1]
    zs = []

    for x in c.xs:
        if isinstance(x, str):
            zs.append(x)
        elif isinstance(x, UseScene):
            zs.append(c.scenes[x.id-1].text)
        else:
            raise Exception
    return "\n".join(zs)

def use(model: str, file: str):
    from storyteller import config, llm, fs

    c = config.load()
    m = c.models[model]
    data = load_context(file)
    content = llm.query(m, data)
    fs.append_text(file, content)

def render(file: str):
    print(load_context(file))

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
