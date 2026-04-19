from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

VERSION = '0.1.0'
DESCRIPTION = 'FC 26 SBC Solver — encontra o squad mais barato para SBCs do EA Sports FC 26'
LONG_DESCRIPTION = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="fc26-sbc-solver",
    version=VERSION,
    author="Nicolas Oliveira",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/nicolaskirvano/fc26-sbc-solver",
    packages=find_packages(where="src"),
    install_requires=[
        "ortools",
        "pandas",
        "prettytable",
    ],
    keywords=[
        'google or-tools',
        'cp-sat',
        'python',
        'fc26',
        'ea-sports-fc',
        'ultimate-team',
        'sbc',
        'squad-building-challenge',
    ],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.12",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    package_dir={"": "src"},
    python_requires=">=3.11",
)
