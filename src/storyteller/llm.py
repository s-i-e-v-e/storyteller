import json

from storyteller.config import Model

def query(m: Model, prompt: str):
    match m.api_type:
        case 'openai':
            return __openai(m, prompt)
        case 'ollama':
            return __ollama(m, prompt)
        case 'kobold':
            return __kobold(m, prompt)
        case 'llamacpp':
            return __llamacpp(m, prompt)
        case _:
            raise Exception

def __ollama(m: Model, prompt: str):
    import requests
    url = f'{m.url}/api/generate'
    in_data = json.dumps({
        'model': m.name,
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
        model=m.name,
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

def __llamacpp(m: Model, prompt: str):
    xs = []
    from storyteller.llamacpp import llamacpp_generate_streaming
    for chunk in llamacpp_generate_streaming(prompt, m.url, m.max_context, m.max_tokens, m.temperature, m.min_p, m.top_p, m.top_k):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

def __kobold(m: Model, prompt: str):
    xs = []
    from storyteller.kobold import koboldcpp_generate_streaming
    for chunk in koboldcpp_generate_streaming(prompt, m.url, m.max_context, m.max_tokens, m.temperature, m.min_p, m.top_p, m.top_k):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

