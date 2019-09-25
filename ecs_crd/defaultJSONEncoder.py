#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from json import JSONEncoder


class DefaultJSONEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__