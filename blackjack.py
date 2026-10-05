from deck import Deck, Card
from server import Server
import time

GAME_STATES = ("Waiting", "In round")
MAX_PLAYERS = 100



class Blackjack:
    def __init__(self):
        self.deck = Deck()
        self.server = Server(game_type = "BlackJack" ,player_allowed=MAX_PLAYERS, rule_function=self.rules)

        self.server.game_state = GAME_STATES[0]
        #self.rules()

        self.players = dict() #{uuid: bet_amount }         #{"Player1": [], "Player2": []}
        #self.bets = dict() #{"Player1": 10, "Player2": 25}

        self.gameplay_loop()

    def rules(self):
        return """
        RULES OF THE BLACKJACK\n\n
        Get as close as 21 as your luck can allow.\n
        At your turn you can: \n
        \t1. Hit: To draw an additional card.\n
        \t2. stand: To skip turn if satisfied with card count.\n
        \n
        No refund policy! ...\n
        No splitting. Casino's rules!\n
        Leaving game for more than 60s will result in automatic loss.\n
        After input have been requested. You have ~60s to answer. I no input given during that time period this is counted as a forfeit.\n
        More that 3 time giving an invalid command will result in a forfeit.\n\n
        """
        #print("\t3. Split: In case of having double the same value card you can split to two hands. (Every additional hand cost same as initial bet)")




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
                self.players[player].append(self.deck.draw())

    def dealer_turn(self, dealer):
        print("\nDealer's turn")
        while self.card_count(dealer) <17:
            dealer.append(self.deck.draw())
        print(f"Dealer end up with: {self.string_hand(dealer)} . For a total of {self.card_count(dealer)}.")

    def debug_print_players_hands(self):
        for player in self.players:
            print(f"{player}'s hand is {self.string_hand(self.players[player])}")

    def end_game(self, dealer):
        for player in self.players:
            card_total = self.card_count(self.players[player])
            if  card_total>21 or card_total< self.card_count(dealer)<=21:
                self.bets[player] = 0
            elif self.card_count(dealer) < card_total :
                self.bets[player] *= 2

        for player in self.bets:
            if self.bets[player] > 0:
                print(f"{player}'s receives: {self.bets[player]}")


    def pregame(self):
        self.server.game_state = GAME_STATES[0]

        self.server.in_game_lock.acquire()
        self.server.in_lobby_lock.acquire()

        self.server.in_game = self.server.in_game + self.server.in_lobby
        self.server.in_lobby = set()

        self.server.in_game_lock.release()
        self.server.in_lobby_lock.release()

        wait = 0
        while wait < 60:
            time.sleep(10)
            wait +=10
            self.server.send_all_in_game(f"Waiting for players. {60-wait}s")
        self.server.send_all_in_game(f"Game starting...")
        self.players = dict()
        for player in self.server.in_game:
            self.players[player] = 0

        self.server.game_state = GAME_STATES[1]

    def get_bets(self):
        self.server.send_all_in_game([1,f"How much do you want to bet?: "], True)

    def gameplay_loop(self):
        self.pregame()
        self.get_bets()

        self.game_state = GAME_STATES[1]
        dealer = [self.deck.draw() , self.deck.draw()] #dealer get two random cards
        print(f"Dealer has drown: {dealer[0]} and one face down.\n")
        self.deal_hands()
        #self.debug_print_players_hands()
        #while not self.end:
        for player in self.players:
            print(f"\n{player}'s turn.")
            while True:
                action = input(f"You have {self.string_hand(self.players[player])}. Total: {self.card_count(self.players[player])}\n->")
                match action.lower():
                    case 'hit':
                        self.players[player].append(self.deck.draw())
                        print(f"{player} has drown {self.players[player][-1]}.")
                        if self.card_count(self.players[player]) >21:
                            print(f"{player} is busted. Total : {self.card_count(self.players[player])}")
                            break

                    case 'stand':
                        print(f"{player} stands.")
                        break
                    case _:
                        print(f'{action} is an invalid action. try "hit" or "stand".')
        #end while

        self.dealer_turn(dealer)
        self.end_game(dealer)
        self.game_state = GAME_STATES[0]


if __name__ == "__main__":
    blackjack = Blackjack()



# cap JQK values to 10 and A 11