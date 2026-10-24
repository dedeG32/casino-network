from deck import Deck, Card
from server import Server
import time

GAME_STATES = ("Waiting", "In round")
MAX_PLAYERS = 100

LOBBY_WAIT_TIME = 10#50 # 20 #50
ACTION_TIMOUT = 30

BLACKJACK_DEBUG = True

class Blackjack:
    def __init__(self):
        self.deck = Deck()
        self.server = Server(player_allowed=MAX_PLAYERS, rule_function=self.rules)

        self.server.game_state = GAME_STATES[0]
        #self.rules()

        self.players = dict() #{uuid: [bet_amount, [card1, card2, ...]] }         #{"Player1": [], "Player2": []}
        #self.bets = dict() #{"Player1": 10, "Player2": 25}

        while True:
            self.gameplay_loop()

    def rules(self):
        return f"""
        RULES OF THE BLACKJACK\n\n
        Get as close as 21 as your luck can allow.\n
        At your turn you can: \n
        \t1. Hit: To draw an additional card.\n
        \t2. stand: To skip turn if satisfied with card count.\n
        \n
        No refund policy! ...\n
        No splitting. Casino's rules!\n
        Leaving game and not returning before second chance will result in a loss.\n
        After input have been requested. You have ~{ACTION_TIMOUT}s to answer. I no input given during that time period this is counted as a forfeit.\n
        More that 3 time giving an invalid command will result in a forfeit.\n\n
        """
        #Leaving game for more than 60s will result in automatic loss.\n
        #print("\t3. Split: In case of having double the same value card you can split to two hands. (Every additional hand cost same as initial bet)")



    def reset_game(self):
        self.deck.reset_deck()
        for player in self.players.keys():
            self.players[player] = dict()


    def string_hand(self, hand:list[Card]):
        str_hand = ""
        for card in hand:
            str_hand = str_hand + str(card) + " "
        return str_hand

    def card_value(self, card:Card):
        if int(card) > 10:
            return 10
        return int(card)

    def card_count(self, hand:list[Card]):
        count = 0
        ace = False
        for card in hand:
            count = count + self.card_value(card)
            if int(card) == 1:
                ace = True

        if ace and count <= 11:
            count = count + 10

        return count

    def deal_hands(self):
        for i in range(2):
            for player in self.players:
                self.players[player][1].append(self.deck.draw())

    def dealer_turn(self, dealer):
        print("\nDealer's turn")
        self.server.send_all_in_game(["\nDealer's turn"])
        while self.card_count(dealer) <17:
            dealer.append(self.deck.draw())
        self.server.send_all_in_game([f"Dealer end up with: {self.string_hand(dealer)} . For a total of {self.card_count(dealer)}."])
        print(f"Dealer end up with: {self.string_hand(dealer)} . For a total of {self.card_count(dealer)}.")

    def debug_print_players_hands(self):
        for player in self.players:
            print(f"{player}'s hand is {self.string_hand(self.players[player])}")

    def end_game(self, dealer):
        dealer_total = self.card_count(dealer)

        for player in self.players.keys():
            card_total = self.card_count(self.players[player][1])
            if card_total > 21: self.players[player][0] = 0
            elif dealer_total > 21 or card_total > dealer_total: self.players[player][0] *= 2
            elif card_total < dealer_total: self.players[player][0] = 0

        self.server.database.get_bets_out_in(self.players, False)

        win_msg = ""
        for player in self.players:
            if self.players[player][0] > 0:
                win_msg += f"{self.server.clients[player][1]} wins {self.players[player][0]} tokens\n"

        self.server.send_all_in_game([win_msg])
        time.sleep(1)


    def pregame(self):
        self.server.game_state = GAME_STATES[0]


        self.server.in_game = self.server.in_game | self.server.in_lobby  #no lock needed hopefully
        self.server.in_lobby = set()                          #no lock needed, at this stage the game is in "waiting" state. The self.server.in_lobby isn't used.

        if BLACKJACK_DEBUG:
            print("Game state:", self.server.game_state)
            print("Players in game:", self.server.in_game)
            print("Players in lobby:", self.server.in_lobby)

        wait = 0
        while wait < LOBBY_WAIT_TIME:
            self.server.send_all(self.server.in_game,[1,f"Waiting for players. {LOBBY_WAIT_TIME - wait}s"])
            time.sleep(5)
            wait +=5


        self.players = dict()

        self.server.game_state = GAME_STATES[1]

        if not self.server.in_game:
            return False

        if BLACKJACK_DEBUG: print(f"server.in_game = {self.server.in_game}, self.player before anything = {self.players}")

        for player in self.server.in_game:
            self.players[player] = [0, list()]

        if BLACKJACK_DEBUG: print("self.players after = ",self.players)

        self.server.send_all(self.server.in_game, [1, f"Game starting..."])
        time.sleep(0.2)

        return True

    def get_bets(self):
        balances = self.server.database.get_balances(self.server.in_game)
        bets = self.server.send_all(self.server.in_game,[2,1,f"How much do you want to bet?: "],  ACTION_TIMOUT, balances)

        remove_players = set()
        for uuid in bets.keys():
            try:
                self.players[uuid] = [int(bets[uuid]), list()]
            except:
                remove_players.add(uuid)


        for player in self.players.keys():
            if self.players[player][0] <= 0 or self.players[player][0] > balances[player]:
                remove_players.add(player)

        if BLACKJACK_DEBUG:print(f"self.players before remove: {self.players}, players to remove: {remove_players}")

        for player in remove_players:
            self.server.move_to_lobby(player, 'Invalid bet.')
            del self.players[player]

        if BLACKJACK_DEBUG: print(f"self.players after remove: {self.players}")

        if not self.players : #empty
            return False

        self.server.database.get_bets_out_in(self.players, True) # substract all those bets from database
        return True


    def gameplay_loop(self):
        self.reset_game()
        AFK_list = list()  # player disconnected od turn skipped
        #while not self.pregame() or not self.get_bets():
        #    print("BLACKJACK: game cannot start. Waiting for players")
         #   continue

        while True:
            if not self.pregame():
                print("DEBUG: pregame returned False")
                continue

            if not self.get_bets():
                print("DEBUG: get_bets returned False")
                continue

            break

        self.game_state = GAME_STATES[1]

        dealer = [self.deck.draw() , self.deck.draw()] #dealer get two random cards

        print(f"GAME: Dealer has drown: {dealer[0]} and one face down.\n")
        self.server.send_all_in_game([f"Dealer has drown: {dealer[0]} and one face down.\n"])

        self.deal_hands()
        #self.debug_print_players_hands()
        #while not self.end:
        for player in self.players.keys():
            self.server.send_all_in_game([f"\n{self.server.clients[player][1]}'s turn."])
            if BLACKJACK_DEBUG: print(f"GAME. {self.server.clients[player][1]}'s turn.")
            while True:
                action_end_time = time.time() + ACTION_TIMOUT
                time.sleep(0.1)
                action = self.server.request_user_input(player, [2,0,f"You have {self.string_hand(self.players[player][1])}. Total: {self.card_count(self.players[player][1])}\n"], action_end_time- time.time())
                #action = input(f"You have {self.string_hand(self.players[player])}. Total: {self.card_count(self.players[player])}\n->")
                if action is None:
                    self.server.send_to_uuid(player,[1,"Timeout. You will have on last chance after players turn."])
                    AFK_list.append(player)
                    break

                match action.lower():
                    case 'hit':
                        big_message = ""
                        self.players[player][1].append(self.deck.draw())
                        big_message += f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}."
                        #self.server.send_all(self.server.in_game-{player},[1,f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}."])
                        print(f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}.")
                        if self.card_count(self.players[player][1]) >21:
                            #self.server.send_all([1,f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}"])
                            big_message += f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}"
                            print(f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}")
                            self.server.send_all(self.server.in_game, [1, big_message])
                            break
                        self.server.send_all(self.server.in_game, [1,big_message])
                        time.sleep(0.2)

                    case 'stand':
                        self.server.send_all_in_game([f"\n{self.server.clients[player][1]} stands."])
                        print(f"{self.server.clients[player][1]} stands.")
                        break
                    case _:
                        self.server.send_to_uuid(player, [1,f'"{action}" is an invalid action. try "hit" or "stand".'])
                        print(f'GAME "{action}" is an invalid action. try "hit" or "stand".')
        #end while
        #AFK turns
        if BLACKJACK_DEBUG: print(f"GAME. AFK users: {AFK_list}")
        Disconnect_list = set()
        for player in AFK_list:
            self.server.send_all_in_game([f"\n{self.server.clients[player][1]}'s turn. (Second chance)"], Disconnect_list)
            if BLACKJACK_DEBUG: print(f"GAME. {self.server.clients[player][1]}'s turn.")
            while True:
                action_end_time = time.time() + ACTION_TIMOUT
                time.sleep(0.1)
                action = self.server.request_user_input(player, [2, 0,
                                                                 f"You have {self.string_hand(self.players[player][1])}. Total: {self.card_count(self.players[player][1])}\n"],
                                                        action_end_time - time.time())
                # action = input(f"You have {self.string_hand(self.players[player])}. Total: {self.card_count(self.players[player])}\n->")
                if action is None:
                    self.server.send_to_uuid(player, [1, "Timeout. You will have on last chance after players turn."])
                    Disconnect_list.add(player)
                    break

                match action.lower():
                    case 'hit':
                        big_message = ""
                        self.players[player][1].append(self.deck.draw())
                        big_message += f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}."
                        # self.server.send_all(self.server.in_game-{player},[1,f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}."])
                        print(f"{self.server.clients[player][1]} has drown {self.players[player][1][-1]}.")
                        if self.card_count(self.players[player][1]) > 21:
                            # self.server.send_all([1,f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}"])
                            big_message += f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}"
                            print(f"{self.server.clients[player][1]} is busted. Total : {self.card_count(self.players[player][1])}")
                            self.server.send_all(self.server.in_game, [1, big_message])
                            break
                        self.server.send_all(self.server.in_game, [1, big_message])
                        time.sleep(0.2)

                    case 'stand':
                        self.server.send_all_in_game([f"\n{self.server.clients[player][1]} stands."])
                        print(f"{self.server.clients[player][1]} stands.")
                        break
                    case _:
                        self.server.send_to_uuid(player, [1, f'"{action}" is an invalid action. try "hit" or "stand".'])
                        print(f'GAME "{action}" is an invalid action. try "hit" or "stand".')
        #end while

        self.dealer_turn(dealer)
        self.end_game(dealer)

        for player in Disconnect_list:
            self.server.disconnect_user(player)

        self.server.game_state = GAME_STATES[0]


if __name__ == "__main__":
    blackjack = Blackjack()



# cap JQK values to 10 and A 11