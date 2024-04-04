import openai 
import os 
import sys 
import subprocess
from stopit import threading_timeoutable as timeoutable

class OpenAI: 
  def __init__(self, model_name='gpt-3.5-turbo'):
      self.client = OpenAI(
          api_key=os.environ["OPENAI_API_KEY"],
      )

  def __call__(self, prompt, temperature=0.1):
      response = self.client.chat.completions.create(
          model=model_name,
          messages=[{"role": "user", "content": prompt}],
          temperature=temperature,
      )
      return response.choices[0].message.content


class suppress_stdout_stderr(object):
    def __enter__(self):
        self.outnull_file = open(os.devnull, 'w')
        self.errnull_file = open(os.devnull, 'w')

        self.old_stdout_fileno_undup    = sys.stdout.fileno()
        self.old_stderr_fileno_undup    = sys.stderr.fileno()

        self.old_stdout_fileno = os.dup ( sys.stdout.fileno() )
        self.old_stderr_fileno = os.dup ( sys.stderr.fileno() )

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        os.dup2 ( self.outnull_file.fileno(), self.old_stdout_fileno_undup )
        os.dup2 ( self.errnull_file.fileno(), self.old_stderr_fileno_undup )

        sys.stdout = self.outnull_file        
        sys.stderr = self.errnull_file
        return self

    def __exit__(self, *_):        
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        os.dup2 ( self.old_stdout_fileno, self.old_stdout_fileno_undup )
        os.dup2 ( self.old_stderr_fileno, self.old_stderr_fileno_undup )

        os.close ( self.old_stdout_fileno )
        os.close ( self.old_stderr_fileno )

        self.outnull_file.close()
        self.errnull_file.close()

class LocalLlama: 
  def __init__(self, gguf_path: str, llama_cpp_path=os.environ['LLAMA']):
    self.llama_cpp_path = llama_cpp_path
    self.gguf_path = gguf_path
    self.flags = { 
        "repeat_penalty": 1.5, 
        "n-gpu-layers": 15000, 
        'ctx_size': 2048
    }

  @timeoutable()
  def __call__(self, prompt: str, flags=None, grammar=None, stop_at="", temperature=0.1, timeout=50):
      if flags: 
        self.flags.update(flags)

      flags = self.flags

      if grammar: 
        with open('./grammar.gnbf', 'w') as f: 
          f.write(grammar)
        self.flags.update({'grammar-file': './grammar.gnbf'})

      self.write_file(prompt)

      with suppress_stdout_stderr():
        output = subprocess.check_output(self.format_command(prompt, flags), shell=True).decode('utf-8')

      if stop_at:
        return output.split(stop_at)[1]

      return output

  def write_file(self, prompt): 
      with open('./prompt.txt', 'w') as f: 
        f.write(prompt) 

  def format_command(self, prompt: str, flags, temperature=0.1):
      return f"{self.llama_cpp_path}/main  --model {self.gguf_path} {" ".join([f"--{k} {v}" for k, v in flags.items()])} --file ./prompt.txt --temp {temperature}"