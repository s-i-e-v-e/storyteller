import dataclasses

import toml
from nonstd import fs

CONFIG_FILE = 'storyteller.toml'

@dataclasses.dataclass
class Model:
    name: str
    url: str
    api_type: str
    api_key: str
    top_p: float
    temperature: float
    max_tokens: int
    keep_alive: str

@dataclasses.dataclass
class Configuration:
    models: dict[str, Model]

def load() -> Configuration:
    if fs.exists(CONFIG_FILE):
        x = toml.loads(fs.read_text(CONFIG_FILE))
    else:
        x = {}

    c = Configuration({})
    for k in x.keys():
        d = x[k]
        c.models[k] = Model(d['name'], d['url'], d['api_type'], d.get('api_key', ''), d.get('top_p', 1.0), d.get('temperature', 1.0), d.get('max_tokens', 4_096), f"{d.get('keep_alive', '10')}m" )

    return c

def store(x: dict):
    fs.write_text(CONFIG_FILE, toml.dumps(x))
