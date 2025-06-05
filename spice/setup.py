from setuptools import setup, find_packages

setup(
    name="spyc",
    version="0.1.0",
    description="A Python Superset with all the Spice",
    author="Reclipse",
    packages=find_packages(where="spice"),
    package_dir={"": "spice"},    entry_points={
        "console_scripts": [
            "spyc=cli.__main__:main",
            "spy=cli.run:run"
        ]
    },
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "colorama>=0.4"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0",
            "mypy>=1.0"
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent"
    ]
)
