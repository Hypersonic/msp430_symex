from setuptools import setup

setup(
    name='msp430_symex',
    version='0.0.1',
    author='Josh Hofing',
    url='https://github.com/Hypersonic/msp430_symex',
    description='Symbolic execution engine for msp430',
    packages=['msp430_symex'],
    install_requires=[
        'z3-solver',
    ]
)
