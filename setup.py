from setuptools import setup, find_packages

setup(
    name='constrain',
    version='0.1.0',
    author='AkshathRaghav',
    author_email='araviki@purdue.edu',
    description='Ensuring parsability of LLM responses in agent chains',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AkshathRaghav/constrain',
    packages=find_packages(),
    install_requires=[
        'pydantic>=1.8.2', 
        'tiktoken>=0.6.0'
        'llama-cpp-python>=0.2.50', 
        'openai>=1.13.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
