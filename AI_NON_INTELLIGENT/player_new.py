"""
This model is insipired by tutor Matt's implementation
self player keeps tracks of the whole board
self player also keeps other two Player, and will perform Maxn search by using those variables
"""

import random
from collections import defaultdict
import math
import numpy as np
import json
import ast

# Game-specific constants:
# borrowed from tutor Matt's implementation
_STARTING_HEXES = {
    'red': {(-3,3), (-3,2), (-3,1), (-3,0)},
    'green': {(0,-3), (1,-3), (2,-3), (3,-3)},
    'blue': {(3, 0), (2, 1), (1, 2), (0, 3)},
}
_FINISHING_HEXES = {
    'red': {(3,-3), (3,-2), (3,-1), (3,0)},
    'green': {(-3,3), (-2,3), (-1,3), (0,3)},
    'blue': {(-3,0),(-2,-1),(-1,-2),(0,-3)},
}

_HEX_STEPS = [(-1,+0),(+0,-1),(+1,-1),(+1,+0),(+0,+1),(-1,+1)]
_MAX_TURNS = 256 # per player
_RANGE = range(-3, 3+1)
_COLOUR = {'red', 'blue', 'green'}

# all weights are positive, simply - reward will give a punishment
# WIN, LOSE, DRAW are not weights, they are direct rewards/punishments
_REWARDS = {"_WIN": 10,
            "_LOSE": -10,
            "_DRAW": -1,}

_DEFAULT_WEIGHTS = {"_EAT": 2,
            "_WILL_EATEN": 2,
            "_EATEN": 5,
            "_>HEXES": 5,
            "_<HEXES": 5,
            "_CLOSE_HEXES": 1,
            "_CLOSE_END": 2,
            "_EXIT": 4,
            "_NUM_ACTION": 0.5
            # how close is "close to end"?
            # "_THRESHOLD_DIST": 4
            }
# with open("weights.json", "r") as f:
#     _WEIGHTS = json.load(f)

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

class AbstractPlayer:
    """
    Abstract class for a player.
    This class has some common methods that all other player classes will use/overwrites
    This class has some varaibles that all other player classes will use

    NOTE: 'colour' passed in by the System is {red, green, blue}
          internal stored 'colour' by each player is {r, g, b}
    """
    def __init__(self, colour):
        # initialise game board state:
        self.hexes = {(q,r) for q in _RANGE for r in _RANGE if -q-r in _RANGE}
        self.board = {qr: ' ' for qr in self.hexes}
        self.scores = {}
        self.nturns  = 0
        self.history = defaultdict(int, {self._snap(): 1})
        for col in _COLOUR:
            for qr in _STARTING_HEXES[col]:
                self.board[qr] = col
            self.scores[col] = 0
        
        self.colour = colour
        # need those variables to give rewards
        # detail in reward functions

    def action(self):
        """
        this is an abstract player, it will do no action
        """
        pass

    def update(self, colour, action):
        atype, ahexes = action
        if atype == "MOVE":
            pre_hex, new_hex = ahexes
            self.board[pre_hex] = ' '
            self.board[new_hex] = colour
        elif atype == "JUMP":
            pre_hex, new_hex = ahexes
            # this is tutor Matt's method for finding intermedia hex
            # my method(in doc string) is too slow compare to this impressive method!
            intermedia_hex = (pre_hex[0]+new_hex[0])//2, (pre_hex[1]+new_hex[1])//2
            self.board[pre_hex] = ' '
            self.board[new_hex] = colour
            self.board[intermedia_hex] = colour
        elif atype == "EXIT":
            self.board[ahexes] = ' '
            self.scores[colour] += 1
        else: # atype == "PASS":
            pass

    def state_eval(self):
        num_hex = 0
        dist = 0
        for qr in self._get_hexes():
            dist += self._exit_dist(qr)
            num_hex += 1
        return num_hex * 7 - dist

    def _available_actions(self):
        """
        A list of currently-available actions for a particular player
        """
        available_actions = []
        for qr in self._get_hexes():
            if qr in _FINISHING_HEXES[self.colour]:
                available_actions.append(("EXIT", qr))
            q, r = qr
            for dq, dr in _HEX_STEPS:
                for i, atype in [(1, "MOVE"), (2, "JUMP")]:
                    tqr = q+dq*i, r+dr*i
                    if tqr in self.hexes:
                        if self.board[tqr] == ' ':
                            available_actions.append((atype, (qr, tqr)))
                            break
        if not available_actions:
            available_actions.append(("PASS", None))
        return available_actions

    def _exit_dist(self, qr):
        """ this tutor Matt's implementation """
        """how many hexes away from a coordinate is the nearest exiting hex?"""
        q, r = qr
        if self.colour == 'red':
            return 3 - q
        if self.colour == 'green':
            return 3 - r
        if self.colour == 'blue':
            return 3 - (-q-r)

    def _copy(self):
        """ this no point of copying an abstract player """
        pass
    
    def _get_hexes(self):
        hexes = []
        for qr in self.hexes:
            if self.board[qr] == self.colour:
                hexes.append(qr)
        return hexes

    def _snap(self):
        """
        code created by tutor Matt
        Capture the current board state in a hashable way
        (for repeated-state checking)
        """
        return (
            # same colour pieces in the same positions
            tuple((qr,p) for qr,p in self.board.items() if p in _COLOUR),
            self.nturns % 3,
        )

class RandomPlayer(AbstractPlayer):
    def __init__(self, colour):
        super().__init__(colour)

    def action(self):
        super().action()
        action_list = self._available_actions()
        index = int(random.random() * len(action_list))
        return action_list[index]

    def update(self, colour, action):
        super().update(colour, action)

class GreedyPlayer(AbstractPlayer):
    """
    this player will only try to exit ASAP
    """
    def __init__(self, colour):
        super().__init__(colour)

    def action(self):
        super().action()
        action_list = self._available_actions()
        move = None
        value = -1000
        for action in action_list:
            if action[0] == "EXIT" or action[0] == "PASS":
                return action

            last_state_value = self.state_eval()
            last_piece_num = len(self._get_hexes())

            player_cp = self.copy()
            player_cp.update(self.colour, action)
            new_state_value = player_cp.state_eval()
            new_piece_num = len(player_cp._get_hexes())

            h_value = new_state_value - last_state_value
            # worst case: I eat an enemey at my _STARTING POINT
            # if I have more than 4 hexes, this is a fantastic situation
            # else, it is just a normal situatiuon(noramlly it's a bad state, as probably it will be eaten back by the opponents)
            h_value += (new_piece_num - last_piece_num)*_DEFAULT_WEIGHTS["_EAT"]
            if value < h_value:
                value = h_value
                move = action
        return move

    def state_eval(self):
        return super().state_eval()

    def update(self, colour, action):
        super().update(colour, action)
    
    def copy(self):
        player_cp = GreedyPlayer(self.colour)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        return player_cp

class MaxNPlayer(AbstractPlayer):
    def __init__(self, colour, eGreedy=0.9, depth=3):
        super().__init__(colour)
        self.opponents = {}
        self.eGreedy = eGreedy
        # for col in _COLOUR:
        #     if col != self.colour and depth != 1:
        #         self.opponents[col] = MaxNPlayer(col, eGreedy, depth-1)
        


    def action(self):
        """
        this method will choose an action based on maxn strategy
        """
        super().action()
        return self.maxn_search(5)[0]

    def update(self, colour, action, keep=True, update=True):
        global _WEIGHTS
        last_value = self.state_eval()
        super().update(colour, action)
        # for opponent, model in self.opponents.items():
        #     if keep:
        #         model.update(colour, action, keep=False, update=False)
        new_value = self.state_eval()
        state = self._snap()
        self.nturns += 1
        self.history[state] += 1
        # with open("counter" +  ".json", 'r') as f:
        #     counter = json.load(f)

        # if new_value - last_value < 0 and update:
        #     for name, value in _WEIGHTS.items():
        #         if random.random() > self.eGreedy:
        #             _WEIGHTS[name] = random.random() * 7
        # if reward != 0 and self.last_action[0] != "PASS":
        #     self.QL.learn(self.last_state, self.last_action, state, reward, True)
        #     self.QL.saveTable(colour)
        # if update:
        #     if max(self.scores.values()) >=4:
        #         for player, score in self.scores.items():
        #             if score >= 4:
        #                 if player != self.colour:
        #                     for name, value in _WEIGHTS.items():
        #                         if random.random() > self.eGreedy:
        #                             _WEIGHTS[name] = random.random() * 7
        #                     with open('weights.json', 'w') as f:
        #                         json.dump(_WEIGHTS, f)
        #                     if "_WIN" not in counter:
        #                             counter["_WIN"] = {}
        #                     if player not in counter["_WIN"]:
        #                         counter["_WIN"][player] = 0
        #                     counter["_WIN"][player] += 1
        #                     with open("counter" +  ".json", 'w') as f:
        #                         json.dump(counter, f)

        #     if self.history[state] >= 4 or self.nturns >= _MAX_TURNS * 3:
        #         for name, value in _WEIGHTS.items():
        #             if random.random() > self.eGreedy:
        #                 _WEIGHTS[name] = random.random() * 7
        #         with open('weights.json', 'w') as f:
        #             json.dump(_WEIGHTS, f)
        #         if "_DRAW" not in counter:
        #             counter["_DRAW"] = 0
        #         counter["_DRAW"] += 1
        #         with open("counter" +  ".json", 'w') as f:
        #             json.dump(counter, f)


    def state_eval(self):
        """
        a state is good => higher chance of winning
        a state is good != a perfect state(i.e, no enemies around or have eaten a lot of opponents)
        if 'win' is the causes, what are some results? i.e, given win, what results are produced?
        if 'win' is the result, what are some causes? i.e, given win, how likely it is caused by something?
        But a probability network is hard to model since we don't have a huge valid date set
        Instead, we will try to give some features and some weights to give a final state value
        most of features can be treated as independent features, e.g. close to each other is independent of will be eaten
        So P(win|S) = P(win|f1)*P(win|f2)*...
        But some of them are dependent. e.g. If I have < 4 pieces, then the weight of 'eat' should be significant large

        features                              | weights   
        ---------------------------------------------------
        relatively close to each other        | 1         
        (only 4 closest hexes counts)                     
        ---------------------------------------------------
        relatively close to end               | 1         
        (only 4 closest hexes counts)                     
        ---------------------------------------------------
        how likely opponents will win         | 1
        (this does not matter for calculating probality of winning give a state, more detail in report)
        ---------------------------------------------------
        how likely will be eaten with depth=2 | 1
        ---------------------------------------------------
        how likely will eat with depth=2      | 1 
        ---------------------------------------------------
        have less than 4 pieces               | 1
        ---------------------------------------------------
        how many have exited                  | 1
        ---------------------------------------------------
        how many avaliable actions            | 1
        ---------------------------------------------------
        """
        pieces = self._get_hexes()
        num_pieces = len(pieces)
        value = 0

        # if no piece left, lose
        if num_pieces == 0 and self.scores[self.colour] < 4:
            return _REWARDS["_LOSE"]

        # else
        # find top 4 pieces
        sorted_pieces = sorted([(qr, self._exit_dist(qr)) for qr in pieces], key=lambda x: x[1])[:5]

        # relatively close to each other
        if (num_pieces > 0):
            for piece in sorted_pieces:
                value += sum(math.sqrt(math.pow(piece[0][0] - qr[0][0], 2) + math.pow(piece[0][1] - qr[0][1], 2)) for qr in sorted_pieces) * _DEFAULT_WEIGHTS["_CLOSE_HEXES"]
            value /= len(sorted_pieces)

            # do we need to use the difference between this state and last state as value?
            # _dist = 0
            # if(_state is not None):
            #     _piece = _state.piece_hexes.copy().pop()
            #     _dist = sum(math.sqrt(math.pow(_piece[0] - qr[0], 2) + math.pow(_piece[1] - qr[1], 2)) for qr in state.piece_hexes)

        # relatively close to end
        value += (num_pieces * 7 - sum(self._exit_dist(qr) for qr in pieces)) * _DEFAULT_WEIGHTS["_CLOSE_END"]

        # no emnemy around
        punishment  = 0
        for q, r in pieces:
            for step_q, step_r in _HEX_STEPS:
                for dist in range(1, 2):
                    qr_t = q+step_q*dist, r+step_r*dist # qr_t = 'target' hex
                    if qr_t in self.hexes and self.board[qr_t] != ' ' and self.board[qr_t] != self.colour:
                        # only care if it can actually jump over
                        for another_q, another_r in _HEX_STEPS:
                            jump_qr = qr_t[0] + another_q, qr_t[1] + another_r
                            if jump_qr in self.hexes and self.board[jump_qr] == ' ':
                                # dist = 1, 2, 3...
                                # the furthur away from this hex, the less likely it will be eaten, thus 1/dist
                                punishment += 1/dist
        value -= punishment * _DEFAULT_WEIGHTS["_WILL_EATEN"]

        # now will treat have > 4 hexes and < 4 hexes as different features
        # but they might be the same, need some experiments
        # eats an enemy
        default_num = len(_STARTING_HEXES[self.colour])
        current_num = num_pieces + self.scores[self.colour]
        if current_num > default_num:
            value += (current_num - default_num) * _DEFAULT_WEIGHTS["_EAT"]
            value += current_num * _DEFAULT_WEIGHTS["_>HEXES"]
        else:
            value -= (current_num - default_num) * _DEFAULT_WEIGHTS["_EATEN"]
            value -= current_num * _DEFAULT_WEIGHTS["_<HEXES"]

        # how many have exited
        value += self.scores[self.colour] * _DEFAULT_WEIGHTS["_EXIT"]

        value -= (6 * num_pieces - len(self._available_actions())) * _DEFAULT_WEIGHTS["_NUM_ACTION"]

        return value

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

    def maxn_search(self, depth):
        action_list = self._available_actions()
        self_colour = self.colour
        move = self.choose_action()
        value = {}
        for col in _COLOUR:
            if col != self_colour:
                temp_player = self.copy()
                temp_player.colour = col
                value[col] = temp_player.state_eval()
        value[self_colour] = self.state_eval()

        if depth == 1:
            return move, value

        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == 'PASS':
                #  or atype == 'EXIT':
                return (atype, ahexes), value

            player_cp = self.copy()
            player_cp.update(self_colour, (atype, ahexes))

            # if atype == 'EXIT':
            #     value[player_colour] = h_state(player_cp.state)
            #     return 

            for col in _COLOUR:
                if col != self_colour:
                    opponent = self.copy()
                    opponent.colour = col
                    reply_action, scores = opponent.maxn_search(depth-1)
                    if value[self_colour] < scores[self_colour]:
                        value = scores.copy()
                        move = (atype, ahexes)
        # if move is None:
        #     move = action_list[0]
        return move, value

    def copy(self):
        player_cp = MaxNPlayer(self.colour, self.eGreedy)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        player_cp.opponents = self.opponents.copy()
        return player_cp

class QLearningPlayer(AbstractPlayer):
    def __init__(self, colour, eGreedy=0.4):
        super().__init__(colour)
        self.QL = QLearningTable(colour, eGreedy=eGreedy)
        self.last_action = []
        self.last_state = None
        self.last_state_val = 0
        self.eGreedy = eGreedy
        self.state_action_history = []

    def action(self):
        if len(self._get_hexes()) == 0:
            return ("PASS", None)

        reward = 0
        state = self._snap()
        self.QL.checkState(state, self._available_actions())
        # if self.nturns >= 3 and self.last_action[0] != "PASS":
        #     reward = sigmoid(self.state_eval() - self.last_state_val)
        #     self.QL.learn(self.last_state, self.last_action, state, reward)

        # create a greedy move
        greedy_player = GreedyPlayer(self.colour)
        greedy_player.board = self.board.copy()
        greedy_player.hexes = self.hexes.copy()
        greedy_player.scores = self.scores.copy()
        self.last_action = self.QL.chooseAction(state, greedy_player.action(), self._available_actions())
        self.last_state = state
        self.last_state_val = self.state_eval()

        return self.last_action
    
    def update(self, colour, action):
        if len(self._get_hexes()) == 0 and self.scores[self.colour] < 4:
            return ("PASS", None)
            
        super().update(colour, action)

        if colour == self.colour and self.state_action_history and self.state_action_history[-1][1][0] != "PASS":
            self.state_action_history.append((self._snap(), action))

        state = self._snap()
        self.nturns += 1
        self.history[state] += 1
        reward = 0
        with open("counter" +  ".json", 'r') as f:
            counter = json.load(f)
        
        # game not end but lost already
        if len(self._get_hexes()) == 0 and self.scores[self.colour] < 4:
            reward = _REWARDS["_LOSE"]
            
            # self.QL.learn(self.last_state, self.last_action, state, reward, True)
            for i in range(len(self.state_action_history), 0, -1):
                state, action = self.state_action_history[i]
                last_state, last_action = self.state_action_history[i-1]
                self.QL.learn(last_state, last_action, state, reward, True)
            self.QL.saveTable(colour) 

            if max(self.scores.values()) >=4:
                for player, score in self.scores.items():
                    if score >= 4:
                        if "_WIN" not in counter:
                            counter["_WIN"] = {}
                        if player not in counter["_WIN"]:
                            counter["_WIN"][player] = 0
                        counter["_WIN"][player] += 1
                        with open("counter" +  ".json", 'w') as f:
                            json.dump(counter, f)
        # game end
        elif max(self.scores.values()) >=4:
            for player, score in self.scores.items():
                if score >= 4:
                    if player != self.colour:
                        reward = _REWARDS["_LOSE"]
                    else:
                        reward = _REWARDS["_WIN"]
                    # self.QL.learn(self.last_state, self.last_action, state, reward, True)
                    for i in range(len(self.state_action_history), 0, -1):
                        state, action = self.state_action_history[i]
                        last_state, last_action = self.state_action_history[i-1]
                        self.QL.learn(last_state, last_action, state, reward, True)
                    self.QL.saveTable(colour) 
                    if "_WIN" not in counter:
                        counter["_WIN"] = {}
                    if player not in counter["_WIN"]:
                        counter["_WIN"][player] = 0
                    counter["_WIN"][player] += 1
                    with open("counter" +  ".json", 'w') as f:
                        json.dump(counter, f)
        # draw
        elif self.history[state] >= 4 or self.nturns >= _MAX_TURNS * 3:
            reward = _REWARDS["_DRAW"]
            # self.QL.learn(self.last_state, self.last_action, state, reward, True)
            for i in range(len(self.state_action_history), 0, -1):
                state, action = self.state_action_history[i]
                last_state, last_action = self.state_action_history[i-1]
                self.QL.learn(last_state, last_action, state, reward, True)
            self.QL.saveTable(colour) 
            # if self.last_action != None:
            #     if "_DRAW" not in counter:
            #         counter["_DRAW"] = 0
            #     counter["_DRAW"] += 1
            #     with open("counter" +  ".json", 'w') as f:
            #         json.dump(counter, f)
            
        #if reward != 0 and self.last_action[0] != "PASS":
 
    def state_eval(self):
        """
        a state is good => higher chance of winning
        a state is good != a perfect state(i.e, no enemies around or have eaten a lot of opponents)
        if 'win' is the causes, what are some results? i.e, given win, what results are produced?
        if 'win' is the result, what are some causes? i.e, given win, how likely it is caused by something?
        But a probability network is hard to model since we don't have a huge valid date set
        Instead, we will try to give some features and some weights to give a final state value
        most of features can be treated as independent features, e.g. close to each other is independent of will be eaten
        So P(win|S) = P(win|f1)*P(win|f2)*...
        But some of them are dependent. e.g. If I have < 4 pieces, then the weight of 'eat' should be significant large

        features                              | weights   
        ---------------------------------------------------
        relatively close to each other        | 1         
        (only 4 closest hexes counts)                     
        ---------------------------------------------------
        relatively close to end               | 1         
        (only 4 closest hexes counts)                     
        ---------------------------------------------------
        how likely opponents will win         | 1
        (this does not matter for calculating probality of winning give a state, more detail in report)
        ---------------------------------------------------
        how likely will be eaten with depth=2 | 1
        ---------------------------------------------------
        how likely will eat with depth=2      | 1 
        ---------------------------------------------------
        have less than 4 pieces               | 1
        ---------------------------------------------------
        """
        pieces = self._get_hexes()
        num_pieces = len(pieces)
        value = 0

        # if no piece left, lose
        if num_pieces == 0 and self.scores[self.colour] < 4:
            return _REWARDS["_LOSE"]

        # else
        # find top 4 pieces
        sorted_pieces = sorted([(qr, self._exit_dist(qr)) for qr in pieces], key=lambda x: x[1])[:5]

        # relatively close to each other
        if (num_pieces > 0):
            for piece in sorted_pieces:
                value += sum(math.sqrt(math.pow(piece[0][0] - qr[0][0], 2) + math.pow(piece[0][1] - qr[0][1], 2)) for qr in sorted_pieces) * _DEFAULT_WEIGHTS["_CLOSE_HEXES"]
            value /= len(sorted_pieces)

            # do we need to use the difference between this state and last state as value?
            # _dist = 0
            # if(_state is not None):
            #     _piece = _state.piece_hexes.copy().pop()
            #     _dist = sum(math.sqrt(math.pow(_piece[0] - qr[0], 2) + math.pow(_piece[1] - qr[1], 2)) for qr in state.piece_hexes)

        # relatively close to end
        value += (num_pieces * 7 - sum(self._exit_dist(qr) for qr in pieces)) * _DEFAULT_WEIGHTS["_CLOSE_END"]

        # no emnemy around
        punishment  = 0
        for q, r in pieces:
            for step_q, step_r in _HEX_STEPS:
                for dist in range(1, 2):
                    qr_t = q+step_q*dist, r+step_r*dist # qr_t = 'target' hex
                    if qr_t in self.hexes and self.board[qr_t] != ' ' and self.board[qr_t] != self.colour:
                        # only care if it can actually jump over
                        for another_q, another_r in _HEX_STEPS:
                            jump_qr = qr_t[0] + another_q, qr_t[1] + another_r
                            if jump_qr in self.hexes and self.board[jump_qr] == ' ':
                                # dist = 1, 2, 3...
                                # the furthur away from this hex, the less likely it will be eaten, thus 1/dist
                                punishment += 1/dist
        value -= punishment * _DEFAULT_WEIGHTS["_WILL_EATEN"]

        # now will treat have > 4 hexes and < 4 hexes as different features
        # but they might be the same, need some experiments
        # eats an enemy
        default_num = len(_STARTING_HEXES[self.colour])
        current_num = num_pieces + self.scores[self.colour]
        if current_num > default_num:
            value += (current_num - default_num) * _DEFAULT_WEIGHTS["_EAT"]
            value += current_num * _DEFAULT_WEIGHTS["_>HEXES"]
        else:
            value -= (current_num - default_num) * _DEFAULT_WEIGHTS["_EATEN"]
            value -= current_num * _DEFAULT_WEIGHTS["_<HEXES"]

        # how many have exited
        value += self.scores[self.colour] * _DEFAULT_WEIGHTS["_EXIT"]

        value -= (6 * num_pieces - len(self._available_actions())) * _DEFAULT_WEIGHTS["_NUM_ACTION"]
        return value


class QLearningTable:

    def __init__(self, colour, learningRate = 0.35, rewardDecay = 0.9, eGreedy = 1):

        # learningRate is the coefficient of the result we add to the previous value every time
        self.learningRate = learningRate
        # rewardDecay is the coefficient of the difference
        self.rewardDecay = rewardDecay
        # eGreedy means it has an eGreedy probability to choose the action based on the qTable
        self.eGreedy = eGreedy
        with open("qTable" +  ".json", 'r') as f:
            self.qTable = json.load(f)

    def chooseAction(self, state, action, action_list):
        # TODO: Decide what action to take based on the qTable
        state = str(state)
        action_list = [action for action in self.qTable[state].keys() if ast.literal_eval(action) in action_list]
        if max(self.qTable[state].values()) == 0 or random.random() < self.eGreedy:
            #random
            if random.random() > 0.4:
                return ast.literal_eval(action_list[int(random.random() * len(action_list))])
            return action

        else:
            return ast.literal_eval(max(action_list, key=lambda x:x[1]))

    def checkState(self, state, action_list):
        # TODO: Check if the state is in the qTable and add it if not
        state = str(state)
        if state not in self.qTable:
            self.qTable[state] = {}
            for action in action_list:
                action = str(action)
                self.qTable[state][action] = 0
        else:
            for action in action_list:
                action = str(action)
                if action not in self.qTable[state]:
                    self.qTable[state][action] = 0

    def learn(self, last_state, action, state, reward, end=False):
        # end = False ?
        # TODO: Update the qTable based on the result of the action using the Q-Learning algorithm
        #print("*******learn********")
        state = str(state)
        last_state = str(last_state)
        action = str(action)
        if not end:
            qTarget = reward + self.rewardDecay*max(self.qTable[state].values())
        else:
            qTarget = reward

        self.qTable[last_state][action] *= 1-self.learningRate
        self.qTable[last_state][action] += self.learningRate * qTarget

    def saveTable(self, colour):
        #print(self.qTable)
        # TODO: Save the qTable into a json file
        with open('qTable' + '.json', 'w') as f:
            json.dump(self.qTable, f)