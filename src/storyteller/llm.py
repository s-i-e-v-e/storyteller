import requests
import json

from storyteller.config import Model

def query(m: Model, prompt: str):
    match m.api_type:
        case 'openai':
            return __openai(m, prompt)
        case 'ollama':
            return __ollama(m, prompt)
        case 'koboldcpp':
            return __cpp(m, prompt, koboldcpp_generate_streaming)
        case 'llamacpp':
            return __cpp(m, prompt, llamacpp_generate_streaming)
        case _:
            raise Exception

def __ollama(m: Model, prompt: str):
    import requests
    url = f'{m.url}/api/generate'
    in_data = json.dumps({
        'model': m.model_name,
        'prompt': prompt,
        'stream': False,
		'keep_alive': m.keep_alive,
        'options': {
            'top_p': m.top_p,
            'temperature': m.temperature,
            'num_predict': m.max_tokens,
        }
    })
    response = requests.post(url, in_data, timeout=300)
    if response.status_code == 200:
        data = response.json()
        return data['response']
    else:
        print(response.status_code)
        print(response.text)
        raise Exception

def __openai(m: Model, prompt: str):
    from openai import OpenAI
    client = OpenAI(api_key=m.api_key, base_url=m.url)

    response = client.chat.completions.create(
        model=m.model_name,
        messages=[{"role": "user", "content": prompt}],
        top_p=m.top_p,
        temperature=m.temperature,
        max_tokens=m.max_tokens,
        stream=True
    )

    xs = []
    for chunk in response:
        if chunk.choices:
            y = chunk.choices[0]
            print(y, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(y)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

def __cpp(m: Model, prompt: str, fn_generate_streaming):
    xs = []
    for chunk in fn_generate_streaming(prompt, m.url, m.max_tokens, m.temperature, m.min_p, m.top_p, m.top_k):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

def koboldcpp_generate_streaming(prompt: str, api_url: str, max_token_length: int, temperature: float, min_p: float, top_p: float, top_k: int):
    url = f"{api_url}/api/extra/generate/stream"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "max_length": max_token_length,
        "temperature": temperature,
        "min_p": min_p,
        "top_p": top_p,
        "top_k": top_k,
        "stream": True  # Important: set to True for streaming
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(data), stream=True) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            for line in response.iter_lines():
                if line:  # Filter out keep-alive new lines
                    try:
                        decoded_line = line.decode('utf-8').replace('event: message', '').replace('data: ', '').strip()
                        if decoded_line:
                            json_data = json.loads(decoded_line)
                            yield json_data["token"]
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error parsing streaming data: {e}, line: {decoded_line}")
                        yield None  # Or handle the error differently (e.g., break)

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Koboldcpp: {e}")
        yield None # Or handle the error differently (e.g., break)

def llamacpp_generate_streaming(prompt: str, api_url: str, max_token_length: int, temperature: float, min_p: float, top_p: float, top_k: int):
    url = f"{api_url}/completion"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "n_predict": max_token_length,
        "temperature": temperature,
        "min_p": min_p,
        "top_p": top_p,
        "top_k": top_k,
        "stream": True  # Important: set to True for streaming
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(data), stream=True) as response:
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            for line in response.iter_lines():
                if line:  # Filter out keep-alive new lines
                    try:
                        decoded_line = line.decode('utf-8').replace('data: ', '').strip()
                        if decoded_line:
                            json_data = json.loads(decoded_line)
                            yield json_data["content"]
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error parsing streaming data: {e}, line: {decoded_line}")
                        yield None  # Or handle the error differently (e.g., break)

    except requests.exceptions.RequestException as e:
        print(f"Error communicating with llamacpp: {e}")
        yield None # Or handle the error differently (e.g., break)