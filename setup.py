from setuptools import setup, find_packages

setup(
    name="a2a-enterprise-gateway-sdk",
    version="1.0.0",
    description="Enterprise Google Agent-to-Agent (A2A v1.0.0) Sovereign Gateway Client SDK & CLI",
    author="Enterprise Gateway Team",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        "console_scripts": [
            "a2a-gateway=a2a_sdk.cli:main",
        ],
    },
    python_requires=">=3.10",
)
