from deck import Deck, Card

class Blackjack:
    def __init__(self):
        self.deck = Deck()
        self.players = {"Player1":[], "Player2":[]}
        self.bets = {"Player1": 10, "Player2": 25}
        self.rules()
        self.gameplay_loop()

    def rules(self):
        print('RULES OF THE BLACKJACK')
        print('Get as close as 21 as you luck can allow.')
        print('At your turn you can: ')
        print("\t1. Hit: To draw an additional card")
        print("\t2. stand: To skip turn if satisfied with card count.")
        #print("\t3. Split: In case of having double the same value card you can split to two hands. (Every additional hand cost same as initial bet)")

        print("\n No refund policy! ...")
        print("No splitting. Casino's rules!")
        print("Leaving game for more than 60s will result in automatic loss")
        print("\n\n")



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

    def gameplay_loop(self):
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


if __name__ == "__main__":
    blackjack = Blackjack()



# cap JQK values to 10 and A 11