#!../venv/bin/python3
import configparser
import sys

import pymongo
from dateutil import parser
from pymongo import MongoClient


def add_actuators(db: MongoClient, config: configparser.ConfigParser) -> None:
    """
    Adds actuators specified in configuration file

    :param db: the MongoClient
    :param config: the configuration parser
    :return: None
    """

    actuators = list()

    # fans
    num_fans = int(config["fans"]["number_small_fans"])

    actuators.extend([{
        "name": "fan" + str(i + 1).zfill(2),
        "type": "fan",
        "state": False
    } for i in range(num_fans)])

    additional_fans = config["fans"]["additional_fans"].split(",")

    actuators.extend([{
        "name": fan,
        "type": "fan",
        "state": False
    } for fan in additional_fans])

    # heater
    num_heaters = int(config["heaters"]["number_heaters"])

    actuators.extend([{
        "name": "heater" + str(i + 1).zfill(2),
        "type": "heater",
        "state": False
    } for i in range(num_heaters)])

    # water
    num_solenoids = int(config["solenoids"]["number_solenoids"])

    actuators.extend([{
        "name": "solenoid" + str(i + 1).zfill(2),
        "type": "water",
        "state": False
    } for i in range(num_solenoids)])

    # lights
    num_lights = int(config["lights"]["number_lights"])

    actuators.extend([{
        "name": "lights" + str(i + 1).zfill(2),
        "type": "lights",
        "state": False
    } for i in range(num_lights)])

    db.actuators.insert_many(actuators)


def add_default_settings(db: MongoClient, config: configparser.ConfigParser) -> None:
    """
    Adds the settings from the configuration file
    :param db: the MongoClient
    :param config: the configuration parser
    :return: None
    """
    lights_start_time = parser.parse(config["settings"]["lights_start_time"])
    lights_end_time = parser.parse(config["settings"]["lights_end_time"])

    default_settings = {
        "is_manual_mode": bool(config["settings"]["manual_mode"]),
        "temperature": {
            "min": int(config["settings"]["min_temperature"]),
            "max": int(config["settings"]["max_temperature"])
        },
        "soil_moisture": {
            "min": int(config["settings"]["min_soil_moisture"]),
            "max": int(config["settings"]["max_soil_moisture"])
        },
        "lights": {
            "start_time": lights_start_time.hour * 3600 + lights_start_time.minute * 60,  # seconds since midnight
            "end_time": lights_end_time.hour * 3600 + lights_end_time.minute * 60
        },
        "watering_times": [],
        "error_flush_times": [],
        "email_addresses": []
    }

    db.settings.insert_one(default_settings)


def create_indexes(db: MongoClient) -> None:
    """
    Creates indexes on the database
    :param db: the MongoClient
    :return: None
    """
    # need this index to make sure all the names are unique
    db.actuators.create_index([("name", pymongo.TEXT)], name="name_index", default_language="english", unique=True)

    # need these indexes because these collections could be large and we always query on name/sensor.type and timestamp
    db.actuators_state_log.create_index([("name", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
                                        name="name_timestamp_index",
                                        default_language="english")
    db.data_readings.create_index([("sensor.type", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
                                  name="type_timestamp_index",
                                  default_language="english")
    db.greenhouse_server_state.create_index([("timestamp", pymongo.DESCENDING)], name="timestamp_index")


def reinitialize_db(config: configparser.ConfigParser, tables: list = None) -> None:
    """
    Initializes the greenhouse database with data or reinitializes it
    :param config: the configuration parser
    :param tables: a list of tables to fill (actuators, settings, etc)
    :return: None
    """

    mongo_uri = config["mongo"]["mongo_uri"]

    if mongo_uri:
        client = MongoClient(mongo_uri)
    else:
        client = MongoClient()

    db = client.greenhouse

    if "actuators" in tables:
        db.actuators.drop()
        add_actuators(db, config)

    if "actuators_state_log" in tables:
        db.actuators_state_log.drop()
        state_log_size = 100 * 1000000
        db.create_collection("actuators_state_log", capped=True, size=state_log_size)

    if "settings" in tables:
        db.settings.drop()
        add_default_settings(db, config)

    if "data_readings" in tables:
        db.data_readings.drop()
        data_readings_size = 350 * 1000000
        db.create_collection("data_readings", capped=True, size=data_readings_size)

    if "greenhouse_server_state" in tables:
        db.greenhouse_server_state.drop()
        pings_size = 5 * 1000000
        db.create_collection("greenhouse_server_state", capped=True, size=pings_size)

    create_indexes(db)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Usage: " + sys.argv[0] + " [configfile] [tables (comma separated)]")
        exit(1)

    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    tables_str = sys.argv[2]

    tables = tables_str.split(",")

    reinitialize_db(config, tables)
