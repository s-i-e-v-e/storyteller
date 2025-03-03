import requests
import json

def koboldcpp_generate_streaming(prompt: str, api_url: str, max_context_length: int, max_token_length: int, temperature: float, top_p: float, top_k: int):
    url = f"{api_url}/api/extra/generate/stream"
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "max_context_length": max_context_length,
        "max_length": max_token_length,
        "temperature": temperature,
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
