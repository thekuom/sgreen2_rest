sgreen2_rest README
==================
This package is the code for the REST API. I highly recommend using PyCharm with this
package. This also helps you stick to PEP8 and avoid spaghetti code nonsense.


Dependencies
------------
### Python3.6 and Virtual Environment
Virtual environment can be either `virtualenv` or `venv`. 
### MongoDB
- make sure the server is running
```
systemctl enable mongod.service
systemctl start mongod.service
```


Installation and Running
------------------------
### Cloning
```
git clone https://github.com/thekuom/sgreen2_rest
```

### Setting up virtual environment
Using `venv`

```
cd sgreen2_rest
python3 -m venv venv
```
Using `virtualenv`
```
cd sgreen2_rest
python3 -m virtualenv venv
```

### Installing
```
venv/bin/pip install -e .
```

### Running the server
```
venv/bin/pserve [configfile]
```

File Tree
---------
```
scripts/
    db_config.ini        : configuration file for reinitializing the db
    reinitialize_db.py   : initializes the db with indexes and initial values
sgreen2_web/             : the python package
    views/               : holds the code controlling the REST API endpoints
        __init__.py      : makes the views folder a python package
        actuators.py
        data_readings.py
        home.py          : the root of the API (does nothing)
        settings.py
    __init__.py          : mostly generated by Pyramid; creates a Pyramid WSGI App
venv/                    : holds virtual environment libraries and binaries
.coveragerc              : controls test coverage report (not used)
.gitignore
CHANGES.txt              : documents version changes (not used)
development.ini          : settings for development mode
MANIFEST.in              : generated by Pyramid
Procfile                  : for Heroku
production.ini           : settings for production mode
pytest.ini               : generated by Pyramid
README.md                : this file
requirements.txt         : requirements for Heroku
rest_api_endpoints.html  : HTML documentation for REST API (open in web browser)
rest_api_endpoints.raml  : RAML documentation for REST API (used to generate rest_api_endpoints.html)
run                      : what Heroku needs to run (make sure to chmod 775)
runapp.py                : Heroku also needs this
setup.py                 : handles python dependencies and installation
```
### Files of Interest

#### db_config.ini File Layout
```
[mongo]
mongo_uri = the mongo uri to use

[fans]
number_small_fans = how many small fans
additional_fans = any additional fans? comma separated

[heaters]
number_heaters = how many heaters

[solenoids]
number_solenoids = how many solenoids

[lights]
number_lights = how many lights

[settings]
manual_mode = should manual mode be True/False?
min_temperature = minimum temperature (F)
max_temperature = maximum temperature (F)
min_soil_moisture = minimum soil moisture (%)
max_soil_moisture = maximum soil moisture (%)
lights_start_time = when to turn lights on
lights_end_time = when to turn lights off
```

#### `scripts/reinitialize_db.py`
This file resets collections in the database. This is useful if we add another setting or if we need to change
how many actuators there are.

#### `sgreen2_web/views/`
These files define the behavior for the different endpoints of the REST API. You can view
the different endpoints by opening `doc.html` in a web browser. The explanation of the
endpoints, the comments in the code, and some understanding of MongoDB should be sufficient 
to understand what I'm doing here.

References
----------
### Deploying to Heroku
https://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/deployment/heroku.html

Known Bugs
----------
Impossible! There has to be bugs somewhere!

Future Development
------------------
1. Add authentication

