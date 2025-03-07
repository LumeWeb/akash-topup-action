from setuptools import setup, find_packages

setup(
    name="akash-topup-action",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest==7.4.3",
        "pytest-cov==4.1.0",
        "python-dateutil>=2.8.2"
    ],
)
