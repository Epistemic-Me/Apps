from setuptools import setup, find_namespace_packages

setup(
    name="bio_age_coach",
    version="0.1.0",
    packages=find_namespace_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "streamlit>=1.24.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.8.0",
        "aiofiles>=23.1.0",
        "openai>=1.0.0"
    ],
    extras_require={
        "test": ["pytest", "pytest-asyncio"]
    }
) 