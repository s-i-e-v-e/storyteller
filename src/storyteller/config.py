import dataclasses

import fs
import toml


@dataclasses.dataclass
class Model:
    model_name: str
    url: str
    api_type: str
    api_key: str
    top_k: int  # 1-MAX where 1 = 100% probability. 0 = disabled
    top_p: float  # 0.0-1.0 where 0.0 = 100% probability. 1.0 = disabled
    min_p: float  # 0.0-1.0 where 1.0 = 100% probability. 0.0 = disabled
    typ_p: float  # 0.0-1.0 where 0.0 = 100% probability. 1.0 = disabled
    temperature: float  # 0.0-5.0 where 0.0 = 100% probability. 1.0 = default
    xtc_t: float  # 1.0 = disabled. If multiple tokens with probability greather then threshold, use xtc_p to remove all except least probable token.
    xtc_p: float  # 1.0 = disabled
    max_context: int
    max_tokens: int
    keep_alive: str  # ollama


@dataclasses.dataclass
class Configuration:
    models: dict[str, Model]


def load(file: str) -> Configuration:
    while not file.startswith("/") and not fs.exists(file):
        file = f"../{file}"
    x = toml.loads(fs.read_text(file))

    c = Configuration({})
    for k in x.keys():
        d = x[k]
        c.models[k] = Model(
            d["model_name"],
            d["url"],
            d["api_type"],
            d.get("api_key", ""),
            d.get("top_k", 0),
            d.get("top_p", 1.0),
            d.get("min_p", 0.0),
            d.get("typ_p", 1.0),
            d.get("temperature", 1.0),
            d.get("xtc_threshold", 1.0),
            d.get("xtc_probability", 1.0),
            d.get("max_context", 8_192),
            d.get("max_tokens", 4_096),
            f"{d.get('keep_alive', '10')}m",
        )

    return c
