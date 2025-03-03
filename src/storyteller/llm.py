import json
import pprint

from storyteller.config import Model

def query(m: Model, prompt: str):
    match m.api_type:
        case 'openai':
            return __openai(m, prompt)
        case 'ollama':
            return __ollama(m, prompt)
        case 'kobold':
            return __kobold(m, prompt)
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
    messages = []
    messages.append(prompt)

    response = client.chat.completions.create(
        model=m.name,
        messages=messages,
        top_p=m.top_p,
        temperature=m.temperature,
        max_tokens=m.max_tokens,
        stream=False
    )
    choice = response.choices[0]
    return choice.message.content

def __kobold(m: Model, prompt: str):
    xs = []
    from storyteller.kobold import koboldcpp_generate_streaming
    for chunk in koboldcpp_generate_streaming(prompt, m.url, 4096, m.max_tokens, m.temperature, m.top_p, m.top_k):
        if chunk:
            print(chunk, end="", flush=True)  # Print chunk by chunk without newline
            xs.append(chunk)
    print() # New line at end of generation
    xs.append('\n')
    return ''.join(xs)

