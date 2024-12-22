from setuptools import setup, find_packages

setup(
    name="findr",
    use_scm_version=True,
    description="An interactive file search tool with advanced features",
    long_description=open("README.mdx").read(),
    long_description_content_type="text/markdown",
    author="Remco Stoeten",
    author_email="stoetenremco.rs@gmail.com",
    url="https://github.com/remcostoeten/findr",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "questionary>=1.10.0",
        "rich>=10.0.0",
        "pathlib>=1.0.1"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "mypy>=0.900",
            "flake8>=3.9",
        ],
    },
    entry_points={
        "console_scripts": [
            "findr=findr.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
)
