from openai import OpenAI
import os
import sys
import subprocess
from stopit import threading_timeoutable as timeoutable
from typing import Dict


class OpenAI:  # pylint: disable=missing-function-docstring
    def __init__(self, model_name: str = 'gpt-3.5-turbo'):
        self.client = OpenAI(
            api_key=os.environ["OPENAI_API_KEY"],
        )
        self.model_name = model_name

    def __call__(self, prompt: str, temperature: float = 0.1) -> str:
        """
        Args:
            prompt (str): The prompt to be passed to the model.
            temperature (float): Higher the temperature, the more creative the output. Default is 0.1.
        """

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content

# Taken from
# https://stackoverflow.com/questions/11130156/suppress-stdout-stderr-print-from-python-functions


class suppress_stdout_stderr(object):
    def __enter__(self):
        self.outnull_file = open(os.devnull, 'w')
        self.errnull_file = open(os.devnull, 'w')

        self.old_stdout_fileno_undup = sys.stdout.fileno()
        self.old_stderr_fileno_undup = sys.stderr.fileno()

        self.old_stdout_fileno = os.dup(sys.stdout.fileno())
        self.old_stderr_fileno = os.dup(sys.stderr.fileno())

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        os.dup2(self.outnull_file.fileno(), self.old_stdout_fileno_undup)
        os.dup2(self.errnull_file.fileno(), self.old_stderr_fileno_undup)

        sys.stdout = self.outnull_file
        sys.stderr = self.errnull_file
        return self

    def __exit__(self, *_):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        os.dup2(self.old_stdout_fileno, self.old_stdout_fileno_undup)
        os.dup2(self.old_stderr_fileno, self.old_stderr_fileno_undup)

        os.close(self.old_stdout_fileno)
        os.close(self.old_stderr_fileno)

        self.outnull_file.close()
        self.errnull_file.close()


class LocalLlama:
    def __init__(
            self,
            gguf_path: str,
            llama_cpp_path: str = os.environ['LLAMA']):
        """
        Initializes a barebones interface between user and llama.cpp
        Why? llama-cpp-python is quite slow. Discussion here: https://www.reddit.com/r/LocalLLaMA/comments/14evg0g/llamacpppython_is_slower_than_llamacpp_by_more/
        """

        self.llama_cpp_path = llama_cpp_path
        self.gguf_path = gguf_path
        self.flags = {
            "repeat_penalty": 1.5,
            "n-gpu-layers": 15000,
            'ctx_size': 2048
        }

    @timeoutable()
    def __call__(
            self,
            prompt: str,
            flags: Dict = None,
            grammar: str = None,
            stop_at: str = "",
            temperature: float = 0.1,
            timeout: int = 50) -> str:
        """
        Args:
            prompt (str): The prompt to be passed to the model.
            flags (Dict): Flags to be passed to the model.
            grammar (str): The grammar to be passed to the model. Needs to be a string in GNBF format.
            stop_at (str): The token at which generation should be stopped.
            temperature (float): The temperature to be passed to the model.
            timeout (int): The timeout for the model. Default is 50 seconds.
        Returns:
            str: The output from the model.
        """

        if flags:
            self.flags.update(flags)

        flags = self.flags

        if grammar:
            with open('./grammar.gnbf', 'w') as f:
                f.write(grammar)
            self.flags.update({'grammar-file': './grammar.gnbf'})

        self.write_file(prompt)

        with suppress_stdout_stderr():
            output = subprocess.check_output(
                self.format_command(
                    prompt, flags), shell=True).decode('utf-8')

        if stop_at:
            return output.split(stop_at)[1]

        return output

    def write_file(self, prompt):
        with open('./prompt.txt', 'w') as f:
            f.write(prompt)

    def format_command(self, prompt: str, flags, temperature=0.1):
        return f"{self.llama_cpp_path}/main  --model {self.gguf_path} {" ".join(
            [f"--{k} {v}" for k, v in flags.items()])} --file ./prompt.txt --temp {temperature}"
