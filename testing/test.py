# standard libraries
pass
# third party libraries
import boto3 as boto
import rethinkdb
# first party libraries
import bocce


class EventsResource(bocce.Resource):

    @classmethod
    def configure(cls, configuration):
        pass

    def __call__(self):
        response = bocce.Response()
        """
        self.authenticate()
        if self.request.method == 'GET':
            pass
        elif self.request.method == 'POST':
            pass
        else:
            pass
        response.body = 'Hello world!'
        """
        response.body = 'Hello world!'
        return response

    def __enter__(self):
        #rethinkdb_configuration = self.configuration.events.rethinkdb
        #self.rethinkdb = RethinkDB(**rethinkdb_configuration)
        return self, {}



app = bocce.Application()
app.routes['/'] = EventsResource
app.serve()
