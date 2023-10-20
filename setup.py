from setuptools import setup, find_packages

setup(
    name='gitgpt',
    version='0.1.0',
    author='ShinChven',
    author_email='shinchven@gmail.com',
    url='https://github.com/ShinChven/git-gpt.git',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'openai',
        'gitpython'
    ],
    entry_points='''
        [console_scripts]
        git-gpt=git_gpt.cli:cli
    ''',
    description='A CLI tool to generate commit messages and issues based on staged Git diffs using OpenAI GPT-3.5-turbo',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='MIT',  # Assuming you are using the MIT License
)
