# RD Bot
This is a Discord bot written in Python.

## Requirements
* Python 3.6 or higher
* PostgreSQL 9 or higher
* Java 13
* [Lavalink](https://github.com/freyacodes/Lavalink)
* Google Chrome
* Chromedriver

## Setup
1. Clone or download the repository.
2. Set up your Lavalink server.
    1. Download the latest `jar` file, which can be found at the bottom of
       [this page](https://github.com/Frederikam/Lavalink).
    2. Add an `application.yml` file in the same directory as the `jar` file.
       An example can be found [here](https://github.com/Frederikam/Lavalink/blob/master/LavalinkServer/application.yml.example).
    3. Change the port, address, and password as desired.
       The default values in the example file above will work as well.
    4. Run the server using `java -jar Lavalink.jar`.
3. Create and set up a virtual environment using `python3 -m venv venv`.
4. Activate your virtual environment using `source venv/bin/activate`.
5. Install all dependencies using `pip3 install -Ur requirements.txt`.
6. Create a copy of `config.ini.example` and rename it to `config.ini`.
7. Replace all values in `config.ini` with your Discord token, PostgreSQL
   database credentials, and Lavalink server values.
8. Create a copy of `alembic.ini.example` and rename it to `alembic.ini`.
9. Go to `sqlalchemy.url` and replace `{username}`, `{password}`, `{host}`, `{port}`, and `{database}` with your
   PostgreSQL credentials.
10. Run `alembic upgrade head`.
11. Run the bot using `python3 main.py`.
