import pymongo
from bson import json_util
from pyramid.response import Response
from pyramid.view import view_config

from sgreen2_web.helpers import process_start_time_end_time, get_timestamp


class RESTActuators(object):
    def __init__(self, request):
        self.request = request

    @view_config(route_name='actuators', request_method='GET', renderer='json')
    def get(self):
        """
        Gets actuators from the database
        :return: a JSON representation of the data
        """
        # sorting by type allows grouping to be done on the actuators more quickly
        # sorting then by name allows for better viewing
        actuators = self.request.db.actuators.find(projection={"_id": 0},
                                                   sort=[("type", pymongo.ASCENDING), ("name", pymongo.ASCENDING)])
        return json_util.loads(json_util.dumps(actuators))

    @view_config(route_name='actuators_state', request_method='GET', renderer='json')
    def get_state(self):
        """
        Gets the state log for an actuators
        :return: a JSON representation of the data
        """

        name = self.request.matchdict["name"]
        actuator = self.request.db.actuators.find_one({"name": name})

        if actuator is None:
            return Response(status_code=404, json_body={
                "message": "actuator '" + name + "' not found"
            })

        # get optional query params
        try:
            start_time, end_time = process_start_time_end_time(self.request)
        except ValueError as err:
            return Response(status_code=400, json_body={
                "message": str(err)
            })

        data = self.request.db.actuators_state_log.find(
            filter={
                "name": name,
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            },
            projection={"_id": 0},
            sort=[("timestamp", pymongo.DESCENDING)])

        return json_util.loads(json_util.dumps(data))

    @view_config(route_name='actuators_state', request_method='PUT')
    def put_state(self):
        """
        Turns on an actuator
        :return: a Pyramid response
        """
        return self.__switch_actuator(True)

    @view_config(route_name='actuators_state', request_method='DELETE')
    def delete_state(self):
        """
        Turns off an actuator
        :return: a Pyramid response
        """
        return self.__switch_actuator(False)

    def __switch_actuator(self, state):
        """
        Switches the actuator state in the database and inserts the change into the log.
        If no change will be made, the call is ignored.
        :param state: the state to change the actuator to
        :return: a Pyramid response
        """

        name = self.request.matchdict["name"]

        # get actuator by name
        actuator = self.request.db.actuators.find_one({"name": name})

        if actuator is None:
            return Response(status_code=404, json_body={"message": "actuator '" + name + "' not found"})

        # don't update databases if state hasn't changed
        if state != actuator["state"]:
            # insert into actuator state log
            self.request.db.actuators_state_log.insert_one({
                "name": actuator["name"],
                "to_state": state,
                "timestamp": get_timestamp()
            })

            # update actuator state
            actuator["state"] = state
            self.request.db.actuators.update_one({
                "name": actuator["name"]
            }, {
                "$set": actuator
            })

        return Response(status_code=204)
