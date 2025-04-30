from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="snpxplex_streamlit",
    version="1.0.0",
    author="Paco",
    author_email="paco@example.com",
    description="Application Streamlit pour l'analyse génétique SNPXPlex",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/your-username/snpxplex_streamlit",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "snpxplex=src.app.main:main",
        ],
    },
)
