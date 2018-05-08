import pymongo
from bson import json_util
from pyramid.response import Response
from pyramid.view import view_config, view_defaults

from sgreen2_web.helpers import process_start_time_end_time, get_timestamp


@view_defaults(route_name="greenhouse_server_state")
class RESTGreenhouseServerState(object):
    def __init__(self, request):
        self.request = request

    @view_config(request_method="GET", renderer="json")
    def get(self):
        """
        Gets list of server states
        :return: a JSON representation of the data
        """
        # get optional query params
        try:
            start_time, end_time = process_start_time_end_time(self.request)
        except ValueError as err:
            return Response(status_code=400, json_body={
                "message": str(err)
            })

        data = self.request.db.greenhouse_server_state.find(
            filter={
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            },
            projection={"_id": 0},
            sort=[("timestamp", pymongo.DESCENDING)])

        return json_util.loads(json_util.dumps(data))

    @view_config(request_method="POST")
    def post(self):
        """
        Adds a server state
        :return: a Pyramid response object
        """
        server_state = {
            "timestamp": get_timestamp(),
            "state": True
        }

        self.request.db.greenhouse_server_state.insert_one(server_state)

        return Response(status_code=201)
