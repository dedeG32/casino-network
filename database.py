import json
import uuid

class Database:
    def __init__(self):
        self.data = dict()
        self.retrieve_data()


    def retrieve_data(self):
        with open("data.json", "r") as file:
            self.users = json.load(file)

    def store_data(self):
        with open("data.json", "w") as file:
            json.dump(self.data, file)

    def generate_uuid(self):
        while True:
            new_uuid =  str(uuid.uuid4())
            if new_uuid not in self.users:
                self.users[new_uuid] = (1500, "User")  # tokens, role
                return new_uuid

    def get_bets_dict(self, value:dict, sub = False):
        for key, value in value.items():
            self.data[key] += -value if sub else value
        self.store_data()

    def get_uuid_data(self, uuid):
        """
        generate new uuid data (new user) if uuid is None
        :param uuid:
        :return:
        """
        if uuid is None:
            uuid = self.generate_uuid()

        return uuid

    def __del__(self):
        self.store_data()


    def is_uuid(self, uuid):
        return uuid in self.users