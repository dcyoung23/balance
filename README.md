# Balance App

This project originated from my [CS50 Final Project](https://www.youtube.com/watch?v=Kz2YUIlyIqU&t=2s) to create a Python web application.  I found the app beneficial enough that I currently run it locally to track my bills and scheduled payments.  Although not an advanced web application it serves as a pretty good tutorial for creating a Python Flask web application with a database back-end.

## Install

Python 3.7.1 is required

pip install -r requirements.txt

## Requirements

The app uses SQLite as the back-end and in order to run the app a new database named `balance.db` needs to be created in the root project folder.  The [schema.sql](schema.sql) script can be used to create the database structure.  [DB Browser for SQLite](https://sqlitebrowser.org/) can be used to create, design, and edit database files compatible with SQLite.