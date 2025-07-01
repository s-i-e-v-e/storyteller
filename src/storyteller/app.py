def fix_demented_path_resolution(mod: str):
    pass
    # import sys
    # import os
    # for i in range(len(sys.path)):
    #    if sys.path[i].endswith(f'{os.sep}src{os.sep}{mod}'):
    #        sys.path[i] = os.sep.join(sys.path[i].split(os.sep)[:-1])
    # print(sys.path)


def print_help():
    """Prints the command-line interface (CLI) help"""
    print("storyteller: A tool for writing stories")
    print("\nCommands:")
    print(
        "  use <path-to-file> <model> - Use a specified language model to process a given file."
    )
    print(
        "                              <model>: The name of the LLM/service to use (e.g., 'koboldcpp', 'llamacpp'). Refer to the storyteller.toml file."
    )
    print(
        "                              <path-to-file>: The path to the file you want to process."
    )
    print(
        "  render <path-to-file>      - Render the given file  in the terminal after resolving all imports."
    )
    print(
        "                              <path-to-file>: The path to the file to render."
    )


def main():
    import sys

    fix_demented_path_resolution("storyteller")
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    import config

    if sys.argv[1] == "--config":
        c = config.load(sys.argv[2])
        xs = []
        xs.append(sys.argv[0])
        xs.extend(sys.argv[3:])
        sys.argv = xs
    else:
        c = config.load("storyteller.toml")

    from runner import render, use

    match sys.argv[1]:
        case "use":
            use(sys.argv[2], sys.argv[3], c)
        case "render":
            render(sys.argv[2])
        case _:
            print("Unknown command: " + sys.argv[1])
            help()


main()
