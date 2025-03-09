# Storyteller

Storyteller is a simple, text-file-based workflow for chatting with LLMs.

Unlike local chat applications with browser uis where your information is stored in a database or json files, you can keep using your existing text editors and version control all your chats, plot ideas and stories.

# SYNTAX

A text file can contain the following:

- `\include <relative/path/to/file>` statements include the contents of the specified file in the prompt being sent to the LLM.

- `\user` starts a user prompt.

- `\assistant` contains the assistant's response. You can modify this or add your own `\assistant` blocks to make the LLM believe that this is its response.

- `\scene` blocks contain scene information. All `\scene`s across the file are pulled out of the text sequence and collected together in a single list.

  They are not included in any prompt unless a `\use-scene <number>` statement makes use of it.

  You can thus put all your scenes in a single file in chronological order and `\include` this file in the first `\user` block.

  You can then call upon specific scenes in any `\user` blocks with a `\use-scene`

# EXAMPLES

Some examples can be found in the `examples` directory. Update the `storyteller.toml` file with the specifics of your LLM host. Run a model on your host. Then add something to the end of the 'chat.md' file under a `\user` block and run storyteller:

    storyteller use chat.md test

# USAGE

1. You might have a project directory. Configure your LLM backends in a `storyteller.toml` file in that directory. Use the `examples/storyteller.toml.template` file for inspiration.
2. Run your local LLM host (ollama/koboldcpp/llama.cpp or any other)
3. Run storyteller in your project directory and point it to your current chapter/chat file (The `model` is the section label in the toml file).
    storyteller use <file> <model>
4. storyteller will parse the file and send the text contents to the LLM host.
5. You can see the streaming output in the terminal.
6. Once the output is complete, storyteller will append the response in the same file under a `\assistant` block.
7. If your editor does not support autoreload, use `CTRL+R` or something similar to reload the text file from disk.
8. As it is plain text, you can modify anything in the entire file at any time.
9. Just note that some hosts support prompt-caching. So, if you modify text too far back, the cache is invalidated and the model will have to evaluate a lot more of the prompt than necessary.

# INSTALLATION PROCEDURE

This project uses Astral's uv to provide a ridiculously simple way to install this python application.

## Step 1
Install uv

    # On macOS and Linux.
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # On Windows.
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

## Step 2
Clone this repository using

    git clone https://github.com/s-i-e-v-e/storyteller.git

Or download [this zip file](https://github.com/s-i-e-v-e/storyteller/archive/refs/heads/main.zip) and extract it somewhere. And give the folder a name like `storyteller`

## Step 3
Within a terminal, switch to the directory which contains the code.

Then run the following command:

    # On macOS and Linux.
    ./install

    # On Windows.
    uv run install

This will install:

- a symlink to the storyteller script in `~/.local/bin` on Linux
- a storyteller.bat file in `C:\Users\<user>\AppData\Local\Programs` on Windows. Add this path to the `PATH` environment variable if you want to use storyteller from any directory.

# Step 4

You can now use `storyteller` in any directory on your computer as long as it has an appropriately configured `storyteller.toml` file.
