#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lbx-utils",
    version="0.1.0",
    author="JD Lien",
    author_email="jdlien@example.com",  # Replace with your actual email
    description="Utilities for working with Brother LBX label files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jdlien/lbx-utils",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "lbx_utils": ["data/label_templates/*", "data/label_examples/*", "data/schema/*"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pillow>=9.0.0",
        "lxml>=5.3.1",
        "lxml-stubs>=0.5.0",
        "colorama>=0.4.6",
        "typer>=0.9.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "lbx-text-edit=lbx_utils.core.lbx_text_edit:main",
            "lbx-create=lbx_utils.core.lbx_create:main",
            "lbx-change=lbx_utils.core.change_lbx:main",
            "lbx-generate-part-image=lbx_utils.core.generate_part_image:app",
            "lbx=lbx_utils.__main__:app",
        ],
    },
)