def fix_demented_path_resolution(mod: str):
    import sys
    for i in range(len(sys.path)):
        if sys.path[i].endswith(f'/src/{mod}'):
            sys.path[i] = '/'.join(sys.path[i].split('/')[:-1])

def replace(model: str, file: str):
    from storyteller import config
    from nonstd import fs

    c = config.load()
    m = c.models[model]


    data = fs.read_text(file)
    ix = data.rfind('\\context')
    iy = data.find('\\end', ix)
    if ix < 0 or iy < 0:
        raise Exception
    ix += len('\\context')

    from storyteller import llm
    content = llm.query(m, data[ix:iy])

    fs.append_text(file, content)

def main():
    import sys
    fix_demented_path_resolution('storyteller')
    print(sys.argv)
    replace(sys.argv[1], sys.argv[2])

main()
