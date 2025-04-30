from setuptools import setup, find_packages

setup(
    name="snpxplex_streamlit",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "src.app": ["static/*"],
        "src.reporting": ["templates/*"],
    },
    install_requires=[
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "plotly>=5.18.0",
        "weasyprint>=60.1",
        "jinja2>=3.1.0",
        "natsort>=8.4.0",
    ],
)
