import time

import pymongo
from bson import json_util
from pyramid.response import Response
from pyramid.view import view_config, view_defaults

from sgreen2_web.helpers import process_start_time_end_time, get_timestamp


@view_defaults(route_name="data_readings")
class RESTDataReadings(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def get(self):
        """
        Returns data readings
        :return: a JSON representation of the data
        """

        if "type" not in self.request.GET.keys():
            return Response(status_code=400, json_body={
                "message": "required param 'type' not met"
            })

        try:
            start_time, end_time = process_start_time_end_time(self.request)
        except ValueError as err:
            return Response(status_code=400, json_body={
                "message": str(err)
            })

        data = self.request.db.data_readings.find(
            filter={
                "sensor.type": self.request.GET.getone("type"),
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            },
            projection={"_id": 0},
            sort=[("sensor.name", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)])

        return json_util.loads(json_util.dumps(data))

    @view_config(request_method="POST")
    def post(self):
        """
        Adds a data reading
        :return: a Pyramid response object
        """
        try:
            if not ("reading" in self.request.json_body and "sensor" in self.request.json_body and
                    "type" in self.request.json_body["sensor"] and "name" in self.request.json_body["sensor"]):
                raise Exception("Required fields not met")

            data_reading = {
                "timestamp": get_timestamp(),
                "reading": float(self.request.json_body["reading"]),
                "sensor": {
                    "type": self.request.json_body["sensor"]["type"],
                    "name": self.request.json_body["sensor"]["name"]
                }
            }

            if "unit" in self.request.json_body:
                unit = self.request.json_body["unit"]

                if data_reading["sensor"]["type"] == "temp" and unit.lower() == "temp_c":
                    data_reading["reading"] = self.__celsius_to_fahrenheit(data_reading["reading"])

                if data_reading["sensor"]["type"] == "soil" and unit.lower() == "soil_raw":
                    data_reading["reading"] = self.__soil_raw_to_percent(data_reading["reading"])

            if data_reading["sensor"]["type"] == "batt":
                if data_reading["reading"] > 5:
                    data_reading["health"] = "good"
                elif data_reading["reading"] > 4:
                    data_reading["health"] = "low"
                else:
                    data_reading["health"] = "critical"

            self.request.db.data_readings.insert_one(data_reading)

            return Response(status_code=201)
        except ValueError:
            return Response(status_code=400, json_body={"message": "data reading must be of type float"})
        except Exception as err:
            return Response(status_code=400, json_body={"message": str(err)})

    @staticmethod
    def __soil_raw_to_percent(reading: float) -> float:
        return min((reading / 1023.0) * 100.0, 100)

    @staticmethod
    def __celsius_to_fahrenheit(temp: float) -> float:
        return (9.0 / 5.0) * temp + 32
