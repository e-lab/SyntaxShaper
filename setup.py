from setuptools import find_packages, setup

setup(
    name="GrammarFlow",
    version="0.1.0",
    author="AkshathRaghav",
    author_email="araviki@purdue.edu",
    description="Ensuring parsability of LLM responses in agent chains",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/e-lab/SyntaxShaper",
    packages=find_packages(),
    install_requires=[
        'pydantic==1.9.0',
        'tiktoken==0.6.0',
        'openai==1.14.1', 
        'stopit==1.1.2',    
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
