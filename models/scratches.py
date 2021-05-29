"""


from json import JSONEncoder

class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

p = Player()
p.id = 4
p.nickname = "Bob"

print(json.dumps(p, cls=MyEncoder))

"""