import json

class PersistentDict(dict):
    def __init__(self, filename):
        self.filename = filename
        try:
            with open(filename, 'r') as fp:
                self.update(json.load(fp))
        except:
            pass

    def save(self):
        with open(self.filename, 'w') as fp:
            json.dump(self, fp)

    def __getitem__(self, key):
        return self.setdefault(key, {})

    def __setitem__(self, key, value):
        super(PersistentDict, self).__setitem__(key, value)

    def __delitem__(self, key):
        super(PersistentDict, self).__delitem__(key)

