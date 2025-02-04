def fix_demented_path_resolution(mod: str):
    import sys
    for i in range(len(sys.path)):
        if sys.path[i].endswith(f'/src/{mod}'):
            sys.path[i] = '/'.join(sys.path[i].split('/')[:-1])

from dataclasses import dataclass
@dataclass
class State:
    xs: str
    index: int

def handle_include(f: str):
    pass

def find_last_context(st: State):
    data = st.xs
    ix = data.rfind('\\context')
    iy = data.find('\\end', ix)
    if ix < 0 or iy < 0:
        raise Exception
    ix += len('\\context')
    return data[ix:iy]

def load_context(st: State):
    from nonstd import fs
    st = State(find_last_context(st), 0)
    while True:
        ix = st.xs.find('\\include ')
        if ix == -1:
            break
        iy = st.xs.find('\n', ix)
        ixx = ix + len('\\include ')
        fn = st.xs[ixx:iy]
        x = fs.read_text(fn)
        st.xs = st.xs[:ix] + x + st.xs[iy:]
    return st.xs

def replace(model: str, file: str):
    from nonstd import fs
    from storyteller import config, llm

    c = config.load()
    m = c.models[model]
    st = State(fs.read_text(file), 0)
    data = load_context(st)
    content = llm.query(m, data)
    fs.append_text(file, content)

def main():
    import sys
    fix_demented_path_resolution('storyteller')
    print(sys.argv)
    replace(sys.argv[1], sys.argv[2])

main()
