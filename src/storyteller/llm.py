import requests
import json

from config import Model
from fs import raise_error

def query(m: Model, prompt: list[dict[str,str]]):
    match m.api_type:
        case 'ollama':
            return generate(m, prompt, ollama_generate_streaming)
        case 'openai':
            return generate(m, prompt, openai_generate_streaming)
        case 'koboldcpp':
            return generate(m, prompt, koboldcpp_generate_streaming)
        case 'llamacpp':
            return generate(m, prompt, llamacpp_generate_streaming)
        case _:
            raise_error("Unknown api_type found in TOML file: "+m.api_type)

def generate(m: Model, prompt: list[dict[str,str]], fn_generate_streaming):
    xs = []
    for chunk in fn_generate_streaming(m, prompt):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

def koboldcpp_generate_streaming(m: Model, messages: list[dict[str,str]]):
    prompt = messages[-1]["content"]
    url = f"{m.url}/api/extra/generate/stream"
    data = {
        "prompt": prompt,
        "max_length": m.max_tokens,
        "temperature": m.temperature,
        "min_p": m.min_p,
        "top_p": m.top_p,
        "top_k": m.top_k,
        "typical": m.typ_p,
        "xtc_threshold": m.xtc_t,
        "xtc_probablilty": m.xtc_p,
        "stream": True  # Important: set to True for streaming
    }
    return __streaming_core(url, data)

def llamacpp_generate_streaming(m: Model, messages: list[dict[str,str]]):
    url = f"{m.url}/v1/chat/completions"
    data = {
        "model": m.model_name,
        "messages": messages,
        "max_tokens": m.max_tokens,
        "temperature": m.temperature,
        "min_p": m.min_p,
        "top_p": m.top_p,
        "top_k": m.top_k,
        "typical_p": m.typ_p,
        "xtc_threshold": m.xtc_t,
        "xtc_probability": m.xtc_p,
        "stream": True,  # Important: set to True for streaming
        "cache_prompt": True,  # Important: set to True for streaming
    }
    return __streaming_core(url, data)

def openai_generate_streaming(m: Model, messages: list[dict[str,str]]):
    url = f"{m.url}/v1/chat/completions"
    data = {
        "model": m.model_name,
        "messages": messages,
        "top_p": m.top_p,
        "max_tokens": m.max_tokens,
        "temperature": m.temperature,
        "stream": True  # Enable streaming
    }
    return __streaming_core(url, data)

def ollama_generate_streaming(m: Model, messages: list[dict[str,str]]):
    url = f'{m.url}/api/chat'
    data = {
        'model': m.model_name,
        'messages': messages,
        'stream': True,
        'keep_alive': m.keep_alive,
        'options': {
            'min_p': m.min_p,
            'top_p': m.top_p,
            'top_k': m.top_k,
            "typical_p": m.typ_p,
            'temperature': m.temperature,
            'num_predict': m.max_tokens,
        }
    }
    return __streaming_core(url, data)

def __streaming_core(url: str, data: dict):
    headers = {"Content-Type": "application/json"}
    try:
        with requests.post(url, headers=headers, data=json.dumps(data), stream=True) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            for line in response.iter_lines():
                if line:  # Filter out keep-alive new lines
                    try:
                        decoded_line = line.decode('utf-8').replace('event: message', '').replace('data: ', '').strip()
                        if decoded_line == "[DONE]": #handle done signal, if present
                            break
                        if decoded_line:
                            json_data = json.loads(decoded_line)
                            if "response" in json_data:
                                yield json_data["response"]
                            elif "content" in json_data:
                                yield json_data["content"]
                            elif "token" in json_data:
                                yield json_data["token"]
                            elif "choices" in json_data and len(json_data["choices"]) > 0:
                                delta = json_data["choices"][0].get("delta")
                                if delta and "content" in delta:
                                    yield delta["content"]
                                elif json_data["choices"][0].get("finish_reason") == "stop":
                                    #Indicates the end of the response, handle as needed.
                                    pass
                                elif "content" in json_data["choices"][0]:
                                    yield json_data["choices"][0]["content"]
                            else:
                                raise_error(f"Unexpected JSON structure: {json_data}")
                    except (json.JSONDecodeError, KeyError) as e:
                        raise_error(f"Error parsing streaming data: {e}, line: {decoded_line}")

    except requests.exceptions.RequestException as e:
        raise_error(f"Error communicating with endpoint: {e}")
