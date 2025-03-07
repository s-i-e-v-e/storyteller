import requests
import json

from storyteller.config import Model

def query(m: Model, prompt: str):
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
            raise Exception

def generate(m: Model, prompt: str, fn_generate_streaming):
    xs = []
    for chunk in fn_generate_streaming(m, prompt):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

def koboldcpp_generate_streaming(m: Model, prompt: str):
    url = f"{m.url}/api/extra/generate/stream"
    data = {
        "prompt": prompt,
        "max_length": m.max_tokens,
        "temperature": m.temperature,
        "min_p": m.min_p,
        "top_p": m.top_p,
        "top_k": m.top_k,
        "stream": True  # Important: set to True for streaming
    }
    return __streaming_core(url, data)

def llamacpp_generate_streaming(m: Model, prompt: str):
    url = f"{m.url}/completion"
    data = {
        "prompt": prompt,
        "n_predict": m.max_tokens,
        "temperature": m.temperature,
        "min_p": m.min_p,
        "top_p": m.top_p,
        "top_k": m.top_k,
        "stream": True,  # Important: set to True for streaming
        "cache_prompt": True,  # Important: set to True for streaming
    }
    return __streaming_core(url, data)

def openai_generate_streaming(m: Model, prompt: str):
    url = f"{m.url}/v1/chat/completions"
    data = {
        "model": m.model_name,
        "messages": [{"role": "user", "content": prompt}],
        "top_p": m.top_p,
        "max_tokens": m.max_tokens,
        "temperature": m.temperature,
        "stream": True  # Enable streaming
    }
    return __streaming_core(url, data)

def ollama_generate_streaming(m: Model, prompt: str):
    url = f'{m.url}/api/generate'
    data = {
        'model': m.model_name,
        'prompt': prompt,
        'stream': True,
        'keep_alive': m.keep_alive,
        'options': {
            'min_p': m.min_p,
            'top_p': m.top_p,
            'top_k': m.top_k,
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
                                print(f"Unexpected JSON structure: {json_data}")
                                raise Exception
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error parsing streaming data: {e}, line: {decoded_line}")
                        yield None  # Or handle the error differently (e.g., break)

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with endpoint: {e}")
        yield None # Or handle the error differently (e.g., break)