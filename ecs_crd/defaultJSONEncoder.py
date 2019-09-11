from json import JSONEncoder

class DefaultJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__