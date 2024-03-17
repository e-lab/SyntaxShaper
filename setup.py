from setuptools import find_packages, setup
import typing


def parse_requirements(filename: str) -> typing.List[str]:
    """
    Load requirements from a pip requirements file
    :param: filename - name of the requirements file to be parsed
    :return: list - list of modules mentioned in the requirements file
    """
    req =  """
        pydantic==1.8.2 
        tiktoken==0.6.0
        llama-cpp-python==0.2.50   
        openai==1.13.0
        isort 
        black 
    """
    line_iter = (line.strip() for line in req.split("\n"))
    return [line for line in line_iter if line and not line.startswith("#")]
    
requirements = [ir for ir in parse_requirements("./requirements.txt")]

setup(
    name="grammarflow",
    version="0.1.0",
    author="AkshathRaghav",
    author_email="araviki@purdue.edu",
    description="Ensuring parsability of LLM responses in agent chains",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/e-lab/SyntaxShaper",
    install_requires=requirements,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
