from referee.game import *
from AI_NON_INTELLIGENT.Player import MaxNPlayer, GreedyPlayer, AlternativeGreedyPlayer, AbstractPlayer
import numpy as np
import ast
import random
import json

i = 0
n = 0
learningRate = 0.1
rewardDecay = 0.7
eGreedy = 1
eGreedy_decay = 0.01

with open("qtable.json", 'r') as f:
    qTable = json.load(f)

def play(players):
    # Set up a new Chexers game and initialise a Red, Green and Blue player
    # (constructing three Player classes including running their .__init__() 
    # methods).
    game = Chexers(debugboard=False)

    # Repeat the following until the game ends
    # (starting with Red as the current player, then alternating):
    curr_player, next_player, prev_player = players
    while not game.over():

        # Ask the current player for their next action (calling their .action() 
        # method)
        action = curr_player.action()
        
        # Validate this action (or pass) and apply it to the game if it is 
        # allowed. Display the resulting game state.
        game.update(curr_player.colour, action)

        # Notify all three players (including the current player) of the action
        # (or pass) (using their .update() methods).
        for player in players:
            player.update(curr_player.colour, action)

        # Next player's turn!
        curr_player,next_player,prev_player=next_player,prev_player,curr_player
    
    print(game.drawmsg, game.score)
    return game.score

class QLearningPlayer(AbstractPlayer):
    def __init__(self, colour, depth=3, eGreedy=0.4):
        super().__init__(colour)
        self.opponents = {}
        self.eGreedy = eGreedy
        self.keep_learning = True
        self.last_state = self._snap()[0]
        self.last_action = None

        if depth != 1:                
            self.QL = QLearningTable(colour, eGreedy=eGreedy)   
        
    def action(self):
        if len(self._get_hexes()) == 0:
            return ("PASS", None)

        self.QL.checkState(self.copy())
        return self.QL.chooseAction(str(sorted(self._snap()[0])), self.choose_action(), self._available_actions())

    def update(self, colour, action):
        if colour == self.colour:
            self.last_state = str(sorted(self._snap()[0]))
            self.last_action = str(action)
        
        super().update(colour, action)

        curr_state = self._snap()[0]
        self.nturns += 1
        self.history[curr_state] += 1
        
        if self.keep_learning:
            # update Q-table
            if self.nturns % 3 == 0:
                reward = self.utility_score()
                self.QL.learn(self.last_state, self.last_action, str(sorted(curr_state)), reward)
                
            # game not end but lost already
            if colour == self.colour and action[1] == None:
                self.keep_learning = False
            # game end
            elif max(self.scores.values()) >=4:
                self.keep_learning = False
            # draw
            elif self.history[curr_state] >= 4 or self.nturns >= 256 * 3:
                self.keep_learning = False
                

    def state_eval(self):
        return MaxNPlayer.state_eval(self)

    def choose_action(self):
        """
        this method will choose an action only based on current state(greedy approach)
        """
        # create a greedy move
        greedy_player = GreedyPlayer(self.colour)
        greedy_player.board = self.board.copy()
        greedy_player.hexes = self.hexes.copy()
        greedy_player.scores = self.scores.copy()
        return greedy_player.action()

    def copy(self):
        player_cp = QLearningPlayer(self.colour, depth=1, eGreedy=self.eGreedy)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        player_cp.last_state = self.last_state
        player_cp.last_action = self.last_action
        
        return player_cp

class QLearningTable:

    def __init__(self, colour, learningRate = 0.35, rewardDecay = 0.9, eGreedy = 1):

        # learningRate is the coefficient of the result we add to the previous value every time
        self.learningRate = learningRate
        # rewardDecay is the coefficient of the difference
        self.rewardDecay = rewardDecay
        # eGreedy means it has an eGreedy probability to choose the action based on the qTable
        self.eGreedy = eGreedy
        self.qTable = qTable
    def chooseAction(self, state, action, action_list):
        # TODO: Decide what action to take based on the qTable
        action_list = [action for action in self.qTable[state].keys() if ast.literal_eval(action) in action_list]
        if max(self.qTable[state].values()) == 0 or random.uniform(0, 1) < self.eGreedy:
            #random
            if random.uniform(0, 1) > 0.4:
                return ast.literal_eval(action_list[int(random.uniform(0, 1) * len(action_list))])
            return action

        else:
            return ast.literal_eval(max(action_list, key=lambda x:x[1]))

    def checkState(self, player):
        # TODO: Check if the state is in the qTable and add it if not
        # for each poosible following states from this state, add to the table
        curr_state = str(sorted(player._snap()[0]))
        if curr_state not in self.qTable:
            self.qTable[curr_state] = {}
        
        if player.colour == 'red':
            order = ['red', 'green', 'blue']
        if player.colour == 'blue':
            order = ['blue', 'red', 'green']
        if player.colour == 'green':
            order = ['green', 'blue', 'red']

        for action in player._available_actions()[:]:
            if action not in self.qTable[curr_state].keys():
                self.qTable[curr_state][str(action)] = 0

            temp_player = AbstractPlayer(order[1])
            temp_player.board = player.board.copy()
            temp_player.update(player.colour, action)
            for action2 in temp_player._available_actions()[:]:

                temp_player2 = AbstractPlayer(order[2])
                temp_player2.board = temp_player.board.copy()
                temp_player2.update(temp_player.colour, action2)
                for action3 in temp_player2._available_actions()[:]:
                    temp_player3 = AbstractPlayer(order[0])
                    temp_player3.board = temp_player2.board.copy()
                    temp_player3.update(temp_player2.colour, action3)

                    new_state = str(sorted(temp_player3._snap()[0]))
                    if new_state not in self.qTable.keys():
                        self.qTable[new_state] = {}
                    for action4 in temp_player3._available_actions():
                        if action4 not in self.qTable[new_state].keys():
                            self.qTable[new_state][str(action4)] = 0

    def learn(self, last_state, action, curr_state, reward):
        """
        given a new state(curr_state),
        what can the last_state learn?
        """
        expected_return = reward + self.rewardDecay*max(self.qTable[curr_state].values())
        self.qTable[last_state][action] *= 1-self.learningRate
        self.qTable[last_state][action] += self.learningRate * expected_return


result = {'r': 0,
          'b': 0,
          'g': 0}
while i < 1000:
    print(i)
    i += 1
    n += 1
    #if n < 100:
    players = (QLearningPlayer("red"), GreedyPlayer('green'), AlternativeGreedyPlayer('blue'))

    # if n<200 and n>=100:
    #     players = (QLearningPlayer("red", learningRate, rewardDecay, eGreedy), QLearningPlayer("green", learningRate, rewardDecay, eGreedy), QLearningPlayer("blue", learningRate, rewardDecay, eGreedy))
    
    # if n < 300 and n>=200:
    #     players = (GreedyPlayer('red'), QLearningPlayer("green", learningRate, rewardDecay, eGreedy), GreedyPlayer("blue"))

    # if n<400 and n>=300:
    #     players = (QLearningPlayer("red", learningRate, rewardDecay, eGreedy), QLearningPlayer("green", learningRate, rewardDecay, eGreedy), QLearningPlayer("blue", learningRate, rewardDecay, eGreedy))

    # if n < 500 and n>=400:
    #     players = (GreedyPlayer('red'), GreedyPlayer("green"), QLearningPlayer("blue", learningRate, rewardDecay, eGreedy))

    # if n<600 and n>=500:
    #     players = (QLearningPlayer("red", learningRate, rewardDecay, eGreedy), QLearningPlayer("green", learningRate, rewardDecay, eGreedy), QLearningPlayer("blue", learningRate, rewardDecay, eGreedy))
    #     n = 0
    #players = (MaxNPlayer("red", eGreedy), GreedyPlayer('green'), GreedyPlayer("blue"))
    _result = play(players)
    if _result['r'] >= 4:
        result['r'] += 1
    elif _result['b'] >= 4:
        result['b'] += 1
    elif _result['g'] >= 4:
        result['g'] += 1
#00005
    eGreedy = 0.01 + (1-0.01)*np.exp(-0.001*i)
    # else:
    #     players = (QLearningPlayer("red", learningRate, rewardDecay, eGreedy), GreedyPlayer('green'), RandomPlayer("blue"))
    #     play(players)
    #     eGreedy = 0.01 + (1-0.01)*np.exp(-0.00005*i)
    
    # n += 1
print(result)
with open("qtable.json", "w") as f:
    json.dump(qTable, f)