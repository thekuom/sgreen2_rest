import os

from pyramid.response import FileResponse
from pyramid.view import view_config

here = os.path.dirname(os.path.abspath(__file__))


@view_config(route_name="home")
def home(request):
    return FileResponse(os.path.join(here, "../../rest_api_endpoints.html"), request=request, content_type="text/html")
