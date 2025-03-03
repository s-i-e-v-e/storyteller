def fix_demented_path_resolution(mod: str):
    import sys
    for i in range(len(sys.path)):
        if sys.path[i].endswith(f'/src/{mod}'):
            sys.path[i] = '/'.join(sys.path[i].split('/')[:-1])

def load_context(file: str):
    from storyteller.parser import parse_file, Context, Scene, UseScene

    parse_context = parse_file(file)
    ys = [x for x in parse_context.xs if isinstance(x, Context)]
    c =  ys[-1]
    # import pprint
    # pprint.pprint(c)
    zs = []

    for x in c.xs:
        if isinstance(x, str):
            zs.append(x)
        elif isinstance(x, UseScene):
            zs.append(c.scenes[x.id-1].text)
        else:
            raise Exception
    return "\n".join(zs)

def replace(model: str, file: str):
    from nonstd import fs
    from storyteller import config, llm

    c = config.load()
    m = c.models[model]
    data = load_context(file)
    content = llm.query(m, data)
    fs.append_text(file, content)

def main():
    import sys
    fix_demented_path_resolution('storyteller')
    print(sys.argv)
    replace(sys.argv[1], sys.argv[2])

main()
