# RD Bot
This is a Discord bot written in Python.

## Requirements
* Python 3.6 or higher
* PostgreSQL 9 or higher

### Optional for Linux
These three packages/libraries are required for the `screenshot` command:
* Firefox
* Xvfb
* Geckodriver


## Setup (Ubuntu)
1. Clone or download the repository.
2. Create and set up a virtual environment using `python3 -m venv venv`.
3. Activate your virtual environment using `source venv/bin/activate`.
4. Install all dependencies using `pip3 install -U -r requirements.txt`.
5. Create a copy of `config.ini.example` and rename it to `config.ini`.
6. Replace all values in `config.ini` with your actual Discord token and
   PostgreSQL database credentials.
7. Run the bot using `python3 main.py`.
