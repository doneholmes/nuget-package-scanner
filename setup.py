import setuptools
import nuget_package_scanner.app

with open("README.md", "r") as fh:
    long_description = fh.read()

REQUIRES = [
    "aiohttp>=3,<4",
    "cchardet>=2.1.6",
    "aiodns>=2.0.0",
    "async-lru>=1.0.2",
    "lxml>=4.5.1",
    "tenacity>=6.2.0",
]

setuptools.setup(
    name=nuget_package_scanner.app.NAME,
    version=nuget_package_scanner.app.VERSION,
    author="Donnie Holmes",
    author_email="donnieh@gmail.com",
    description="Scans a github org for Nuget dependencies and builds a currency report",
    keywords="nuget github org dependencies currency report",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/doneholmes/nuget-package-scanner",
    install_requires=REQUIRES,
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8.2',
)