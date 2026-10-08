import json
import uuid

class Database:
    def __init__(self):
        self.data = dict()
        self.retrieve_data()


    def retrieve_data(self):
        with open("data.json", "r") as file:
            self.data = json.load(file)

    def store_data(self):
        with open("data.json", "w") as file:
            json.dump(self.data, file)

    def _generate_uuid(self):
        while True:
            new_uuid =  str(uuid.uuid4())
            if new_uuid not in self.data:
                self.data[new_uuid] = (1500, "User")  # tokens, role
                self.store_data()
                return new_uuid

    def get_bets_out_in(self, value:dict, sub = False):
        for uuid, player_info in value.items():
            self.data[uuid] += -player_info[0] if sub else player_info[0] # player_info[0] is the bet amount
        self.store_data()

    def get_uuid_data(self, uuid):
        """
        generate new uuid data (new user) if uuid is None
        :param uuid:
        :return:
        """
        uuid_x=uuid
        if uuid is None:
            uuid_x = self._generate_uuid()

        return uuid_x

    def __del__(self):
        self.store_data()


    def is_uuid(self, uuid):
        return uuid in self.data