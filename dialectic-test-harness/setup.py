from setuptools import setup, find_packages

setup(
    name="dialectic-harness",
    version="0.1.0",
    description="A test harness for evaluating dialectic learning systems",
    author="Epistemic Me",
    author_email="info@epistemic.me",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0",
        "gym>=0.26.0",
        "torch>=2.0.0",
        "wandb>=0.15.0",
        "transformers>=4.30.0",
        "openai>=1.0.0",  # Added for belief analysis
    ],
    dependency_links=[
        "../Python-SDK#egg=epistemic-me-sdk",  # Use local SDK
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "flake8>=4.0.0",
            "mypy>=1.0.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
) 