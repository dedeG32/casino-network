import json
import uuid

DEBUG_DATABASE = True

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
                self.data[new_uuid] = [1500, "User"]  # tokens, role
                self.store_data()
                return new_uuid


    def get_bets_out_in(self, value: dict, sub=False):
        if DEBUG_DATABASE: print("received those values as bet", value)
        for player_uuid, player_info in value.items():
            bet = player_info[0]
            balance, role = self.data[player_uuid]
            self.data[player_uuid] = [balance + (-bet if sub else bet), role]

        self.store_data()
    def is_uuid_else_generate(self, uuid):
        """
        generate new uuid data (new user) if uuid is None
        :param uuid:
        :return:
        """
        if uuid is None:
            uuid = self._generate_uuid()

        return uuid

    def get_balances(self, uuid):
        return self.data[uuid][0]

    def get_balances(self, uuids):
        balances = dict()
        for uuid in uuids:
            balances[uuid] = self.data[uuid][0]
        return balances

    def __del__(self):
        self.store_data()


    def is_uuid(self, uuid):
        return uuid in self.data