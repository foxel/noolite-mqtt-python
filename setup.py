import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="noolite-mqtt",
    version="0.0.6",
    author="Andrey F. Kupreychik",
    author_email="foxel@quickfox.ru",
    description="NooLite MQTT binding",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/foxel/noolite-mqtt-python",
    packages=['noolite_mqtt'],
    install_requires=[
        'pyserial',
        'paho-mqtt',
    ],
    scripts=[
        'noolite_mqtt/noolite_cli.py',
        'noolite_mqtt/noolite_f_cli.py',
        'noolite_mqtt/noolite_rx_bind.py',
    ],
    entry_points={
        'console_scripts': [
            'noolite-mqtt=noolite_mqtt:cli',
        ],
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
