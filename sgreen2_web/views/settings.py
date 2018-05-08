import pymongo
from bson import json_util
from dateutil import parser
from pyramid.response import Response
from pyramid.view import view_config, view_defaults
from validate_email import validate_email


@view_defaults(route_name="settings")
class RESTSettings(object):
    def __init__(self, request):
        self.request = request

    @staticmethod
    def __get_time_as_string(seconds_since_midnight: int) -> str:
        """
        Converts seconds since midnight to hour, minute tuple
        :param seconds_since_midnight: seconds since midnight
        :return: a tuple of (hour, minute)
        """
        if seconds_since_midnight is None:
            return ""

        hour = int(seconds_since_midnight / 3600)
        minute = int((seconds_since_midnight - hour * 3600) / 60)

        return str(hour).zfill(2) + ":" + str(minute).zfill(2)

    @staticmethod
    def __string_list_to_time_list(times_array) -> list:
        for i in range(len(times_array)):
            parsed_time = parser.parse(times_array[i])
            times_array[i] = parsed_time.hour * 3600 + parsed_time.minute * 60

        return times_array

    @view_config(request_method="GET", renderer="json")
    def get(self):
        """
        Gets settings
        :return: a JSON representation of the data
        """

        # in MongoDB, _id has a timestamp embedded so sorting by _id descending gets the most recent
        data = self.request.db.settings.find_one(projection={"_id": 0}, sort=[("_id", pymongo.DESCENDING)])

        if data is None:
            data = {
                "is_manual_mode": False,
                "temperature": {
                    "min": "",
                    "max": ""
                },
                "soil_moisture": {
                    "min": "",
                    "max": ""
                },
                "lights": {
                    "start_time": None,
                    "end_time": None
                },
                "watering_times": [],
                "error_flush_times": [],
                "email_addresses": []
            }

        # format times as strings
        data["lights"]["start_time"] = self.__get_time_as_string(data["lights"]["start_time"])
        data["lights"]["end_time"] = self.__get_time_as_string(data["lights"]["end_time"])

        for i in range(len(data["watering_times"])):
            data["watering_times"][i] = self.__get_time_as_string(data["watering_times"][i])

        for i in range(len(data["error_flush_times"])):
            data["error_flush_times"][i] = self.__get_time_as_string(data["error_flush_times"][i])

        return json_util.loads(json_util.dumps(data))

    @view_config(request_method="POST", renderer="json")
    def post(self):
        """
        Updates or inserts settings if it doesn't exist
        :return: a Pyramid response object
        """
        try:
            post_data_result = self.__validate_post_data_types()

            data = post_data_result["data"]
            error = post_data_result["error"]

            if error:
                raise Exception(error)

            if data["soil_moisture"]["min"] < 0 or data["soil_moisture"]["max"] < 0:
                raise Exception("soil moisture must be positive")

            if data["temperature"]["min"] >= data["temperature"]["max"]:
                raise Exception("minimum temperature must be less than maximum temperature")

            if data["soil_moisture"]["min"] >= data["soil_moisture"]["max"]:
                raise Exception("minimum soil moisture must be less than maximum soil moisture")

            if "email_addresses" in data:
                for email in data["email_addresses"]:
                    if not validate_email(email):
                        raise Exception(email + " is not a valid email address")
            else:
                data["email_addresses"] = list()

            data["watering_times"].sort()
            data["error_flush_times"].sort()

            # update many with no filtering b/c I only expect one document in the collection
            self.request.db.settings.update_many({}, {"$set": data}, upsert=True)

            return json_util.loads(json_util.dumps(data))
        except Exception as err:
            return Response(status_code=400, json_body={"message": str(err)})

    def __validate_post_data_types(self):
        """
        Makes sure the data that was passed to the POST endpoint are of the right data type
        :return: a dict with data and any errors
        """
        data = dict()
        error = ""
        try:
            data = self.request.json_body

            data["temperature"]["min"] = int(data["temperature"]["min"])
            data["temperature"]["max"] = int(data["temperature"]["max"])

            data["soil_moisture"]["min"] = int(data["soil_moisture"]["min"])
            data["soil_moisture"]["max"] = int(data["soil_moisture"]["max"])

            lights_start_time = parser.parse(data["lights"]["start_time"])
            data["lights"]["start_time"] = lights_start_time.hour * 3600 + lights_start_time.minute * 60

            lights_end_time = parser.parse(data["lights"]["end_time"])
            data["lights"]["end_time"] = lights_end_time.hour * 3600 + lights_end_time.minute * 60

            data["watering_times"] = self.__string_list_to_time_list(data["watering_times"])
            data["error_flush_times"] = self.__string_list_to_time_list(data["error_flush_times"])
        except ValueError:
            error = "Check data formats: temperature and soil moisture must be integers. " \
                    "Time formats must be commonly supported."
        except Exception as err:
            error = str(err)

        return {"data": data, "error": error}
