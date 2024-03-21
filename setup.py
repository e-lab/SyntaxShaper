from setuptools import find_packages, setup
import typing


def parse_requirements(filename: str) -> typing.List[str]:
    req =  """
        pydantic==1.9.0
        tiktoken==0.6.0
        llama-cpp-python==0.2.50   
        openai==1.14.1
    """
    line_iter = (line.strip() for line in req.split("\n"))
    return [line for line in line_iter if line]
    
requirements = parse_requirements("./requirements.txt")

setup(
    name="GrammarFlow",
    version="0.0.7",
    author="AkshathRaghav",
    author_email="araviki@purdue.edu",
    description="Ensuring parsability of LLM responses in agent chains",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/e-lab/SyntaxShaper",
    requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8, <3.10",
)
