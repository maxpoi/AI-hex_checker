"""
This model is insipired by tutor Matt's implementation
self player keeps tracks of the whole board
"""

"""
my own old method for finding jumped over hexes:
def find_jump_over_hex(hexes):
    for x_step, y_step in HEX_STEPS:
        hex = hexes[0][0]+x_step, hexes[0][1]+y_step
        check_hex = hex[0]+x_step, hex[1]+y_step
        if check_hex == hexes[1]:
            return hex
"""

import random
from collections import defaultdict
import math

# Game-specific constants:
# borrowed from tutor Matt's implementation
_STARTING_HEXES = {
    'red': {(-3,3), (-3,2), (-3,1), (-3,0)},
    'green': {(0,-3), (1,-3), (2,-3), (3,-3)},
    'blue': {(3, 0), (2, 1), (1, 2), (0, 3)},
}
_FINISHING_HEXES = {
    'red': {(3,-3), (3, -2), (3, -1), (3,0)},
    'green': {(-3,3), (-2, 3), (-1, 3), (0,3)},
    'blue': {(-3,0),(-2, -1),(-1, -2),(0,-3)},
}

_CORNER_HEXES = {
    'red': {(3,-3), (3,-2), (0, 3), (0, -3)},
    'green': {(-3,3), (-3,0), (3, 0), (0,3)},
    'blue': {(-3,0),(-3,3),(3,-3),(0,-3)},
}

_HEX_STEPS = [(-1,+0),(+0,-1),(+1,-1),(+1,+0),(+0,+1),(-1,+1)]
_MAX_TURNS = 256 # per player
_RANGE = range(-3, 3+1)
_COLOUR = ['red', 'green', 'blue']

# all weights are positive, simply -reward will give a punishment weight
# WIN, LOSE, DRAW are not weights, they are direct rewards/punishments
_REWARDS = {"_WIN": 10000,
            "_LOSE": -10000,
            "_DRAW": -1000,}

_DEFAULT_WEIGHTS = {"_EAT": 3,
            "_WILL_EATEN": 2,
            "_EATEN": 4,
            "_EAT_BACK": 1,
            "_>HEXES": 1,
            "_<HEXES": 5,
            "_CLOSE_HEXES": 4,
            "_CLOSE_END": 5,
            "_EXIT": 40,
            "_NUM_ACTION": 1,
            "_IN_CORNER": 4, 
            "_WILL_EXIT": 5, 
            "_STAY_TOO_LONG": 5
            # how close is "close to end"?
            # "_THRESHOLD_DIST": 4
            }

class AbstractPlayer:
    """
    Abstract class for a player.
    This class has some common methods that all other player classes will use/overwrites
    This class has some varaibles that all other player classes will use
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
        """
        default state evaluation function, just measures how far I am to the end
        """
        dist = 0
        for qr in self._get_hexes():
            dist += self._exit_dist(qr)
        return len(self._get_hexes()) * 7 - dist

    def utility_score(self):
        """
        return sum of the difference between me and others' state value as utility score
        """
        value = 0
        self_state = self.state_eval()
        self_colour = self.colour
        for col in _COLOUR:
            if col != self.colour:
                self.colour = col
                value += self_state - self.state_eval()
        self.colour = self_colour
        return value

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
        """
        NOTE: this tutor Matt's implementation
        how many hexes away from a coordinate is the nearest exiting hex?
        """
        q, r = qr
        if self.colour == 'red':
            return 3 - q
        if self.colour == 'green':
            return 3 - r
        if self.colour == 'blue':
            return 3 - (-q-r)

    def copy(self):
        """
        copy and return an Abstratc Player 
        """
        player = AbstractPlayer(self.colour)
        player.hexes =self.hexes
        player.board = self.board
        return player
    
    def _get_hexes(self):
        """
        return  a list of my own hexes
        """
        h = []
        for qr in self.hexes:
            if self.board[qr] == self.colour:
                h.append(qr)
        return h

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
    this player will only try to exit ASAP or jumpover someone
    this player uses the same evaluation function as the maxn and qlearning players
    but it evaluates the state immediately after taking an action, yet the maxn and qlearning players only evaluates the state after a complete turn
    """
    def __init__(self, colour):
        super().__init__(colour)

    def action(self):
        """
        choose an action based on the difference of the current state and the immediate following state
        i. e. f(s) - f(s | a)
        """
        action_list = self._available_actions()
        move = None
        value = -1000000
        for action in action_list:
            if action[0] == "EXIT" or action[0] == "PASS":
                return action

            last_state_value = self.state_eval()
            # last_piece_num = len(self._get_hexes())

            player_cp = self.copy()
            player_cp.update(self.colour, action)
            new_state_value = player_cp.state_eval()

            h_value = new_state_value - last_state_value
            if value < h_value:
                value = h_value
                move = action
        return move

    def state_eval(self):
        return MaxNPlayer.state_eval(self)

    def update(self, colour, action):
        super().update(colour, action)
    
    def copy(self):
        player_cp = GreedyPlayer(self.colour)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        return player_cp

# test class
class AlternativeGreedyPlayer(AbstractPlayer):
    """
    this is used for testing different state evaluation functions
    it evaluates actions instead of states.
    Even though this seems to be less likely to be a good bot, but it performs well enough to other basic bots
    """
    def __init__(self, colour):
        super().__init__(colour)
    
    def action(self):
        action_list = self._available_actions()

        min_h = _REWARDS["_WIN"]
        final_action = None
        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == 'PASS' or atype == 'EXIT':
                return (atype, ahexes)

            # check if it eats any enemy
            last_num_hexes = len(self._get_hexes()) + self.scores[self.colour]
            temp_player = self.copy()
            temp_player.update(self.colour, (atype, ahexes))
            new_num_hexes = len(temp_player._get_hexes()) + temp_player.scores[self.colour]
            reward = new_num_hexes - last_num_hexes

            # check if any ally may be eaten
            src, dest = ahexes
            punishment = 0
            for i in range(1, 3):
                for x_step, y_step in _HEX_STEPS:
                    neighbour = dest[0] + x_step*i, dest[1] + y_step*i
                    if neighbour in temp_player.hexes and self.board[neighbour] != self.colour and self.board[neighbour] != ' ':
                        punishment += 1/i

            h_value = sum(self._exit_dist(qr)/2 for qr in self._get_hexes()) - 10*reward + punishment
            if h_value < min_h:
                min_h = h_value
                final_action = (atype, ahexes)
        return final_action
    
    def update(self, colour, action):
        super().update(colour, action)
        
    def copy(self):
        player_cp = AlternativeGreedyPlayer(self.colour)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        return player_cp

class MaxNPlayer(AbstractPlayer):
    """
    this bot uses a MaxN search to find the best move
    """
    def __init__(self, colour, depth=3): # depth = 3 means 3 players.
        super().__init__(colour)
        self.opponents = {}
        self.depth = depth
        for col in _COLOUR:
            if col != self.colour and depth != 1:
                self.opponents[col] = MaxNPlayer(col, depth=depth-1)
        
    def action(self):
        """
        this method will choose an action based on maxn strategy
        """
        super().action()
        return self.maxn_search(3)[0]

    def update(self, colour, action, update=True):
        super().update(colour, action)

        curr_state = self._snap()[0]
        self.nturns += 1
        self.history[curr_state] += 1

        for opponent, model in self.opponents.items():
            if update:
                model.update(colour, action, not update)

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
        this is the same saying how many are in danger                
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
        how many hexes in the spots?          | 1
        ---------------------------------------------------
        ...
        """

        pieces = self._get_hexes()
        num_pieces = len(pieces)
        value = 0

        # if no piece left, lose
        if num_pieces == 0:
            if self.scores[self.colour] < 4:
                return _REWARDS["_LOSE"]
            else:
                return _REWARDS["_WIN"]

        # start calculate scores
        # try to capture the perfect spots!
        for qr in pieces:
            if qr in _CORNER_HEXES[self.colour]:
                value += 1 * _DEFAULT_WEIGHTS["_IN_CORNER"]
            if qr in _FINISHING_HEXES[self.colour]:
                value += 1 * _DEFAULT_WEIGHTS["_WILL_EXIT"]
            if qr in _STARTING_HEXES and self.nturns >= _MAX_TURNS * 3/4:
                value -= 1 *_DEFAULT_WEIGHTS["_STAY_TOO_LONG"]
        # else
        # find top 4 pieces
        sorted_pieces = sorted([(qr, self._exit_dist(qr)) for qr in pieces], key=lambda x: x[1])[:5]

        # relatively close to each other
        # how many are in danger
        for qr, dist in sorted_pieces:
            num_ally = 0
            num_enenmy = 0
            for step_q, step_r in _HEX_STEPS:
                next_qr = qr[0] + step_q, qr[1] + step_r
                if next_qr in self.hexes and self.board[next_qr] != ' ':
                    if self.board[next_qr] == self.colour:
                        num_ally += 1
                    else:
                        num_enenmy += 1
            value += _DEFAULT_WEIGHTS["_CLOSE_HEXES"] * (num_ally - num_enenmy)

        """
        last feature is essitentially the combination of the following two features
        but they may weight differently, so only commenting them out insteaf of deleting them
        """
        # if (num_pieces > 0):
        #     for piece in sorted_pieces:
        #         value += sum(math.sqrt(math.pow(piece[0][0] - qr[0][0], 2) + math.pow(piece[0][1] - qr[0][1], 2)) for qr in sorted_pieces) * _DEFAULT_WEIGHTS["_CLOSE_HEXES"]
        #     value /= len(sorted_pieces)

            # do we need to use the difference between this state and last state as value?
            # _dist = 0
            # if(_state is not None):
            #     _piece = _state.piece_hexes.copy().pop()
            #     _dist = sum(math.sqrt(math.pow(_piece[0] - qr[0], 2) + math.pow(_piece[1] - qr[1], 2)) for qr in state.piece_hexes)

        # no emnemy around
        # punishment  = 0
        # for q, r in pieces:
        #     for step_q, step_r in _HEX_STEPS:
        #         for dist in range(1, 2):
        #             qr_t = q+step_q*dist, r+step_r*dist # qr_t = 'target' hex
        #             if qr_t in self.hexes and self.board[qr_t] != ' ' and self.board[qr_t] != self.colour:
        #                 # only care if it can actually jump over
        #                 for another_q, another_r in _HEX_STEPS:
        #                     jump_qr = qr_t[0] + another_q, qr_t[1] + another_r
        #                     if jump_qr in self.hexes and self.board[jump_qr] == ' ':
        #                         # dist = 1, 2, 3...
        #                         # the furthur away from this hex, the less likely it will be eaten, thus 1/dist
        #                         punishment += 1/dist
        # value -= punishment * _DEFAULT_WEIGHTS["_WILL_EATEN"]

        # now will treat have > 4 hexes and < 4 hexes as different features
        # but they might be the same, need some experiments
        # eats an enemy
        default_num = len(_STARTING_HEXES[self.colour])
        current_num = num_pieces + self.scores[self.colour]
        if current_num > default_num:
            value += (current_num - default_num) * _DEFAULT_WEIGHTS["_>HEXES"]
        else:
            value -= (default_num - current_num) * _DEFAULT_WEIGHTS["_<HEXES"]

        # how many have exited
        value += self.scores[self.colour] * _DEFAULT_WEIGHTS["_EXIT"]

        # relatively close to end
        value += (len(sorted_pieces)*6 - sum(self._exit_dist(qr[0])/2 for qr in sorted_pieces)) * _DEFAULT_WEIGHTS["_CLOSE_END"]

        # this feature is too hard to optimize, most of the time it is just useless 
        # value -= (6 * num_pieces - len(self._available_actions())) * _DEFAULT_WEIGHTS["_NUM_ACTION"]
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

    def sort_action(self):
        """
        sort the action based on predefined order
        Or maybe simply only check whether it jumps over an enemy or not will be enough
        But definatly can't sort the action based on the difference between 2 state values
        Because a state might be bad, but it is the only way to survive and win.
        """
        
        actions = [[action, 0] for action in self._available_actions()]
        if actions[0][0][0] == "PASS":
            return self._available_actions()

        adjust_weight = 0
        # adjust some weights depend on various situations, such as potential of losing or draw
        if self.scores[self.colour] + len(self._get_hexes()) < 4:
            adjust_weight = 2

        for i in range(len(actions)):
            action = actions[i][0]

            if action[0] == "EXIT":
                actions[i][1] == 100
                continue
            
            temp_player = self.copy()
            temp_player.update(self.colour, action)
            new_pieces = temp_player._get_hexes()

            # hex_difference
            actions[i][1] += (len(new_pieces) - len(self._get_hexes()))*(_DEFAULT_WEIGHTS["_EAT"] + adjust_weight)

            # if it captures a goooooood spot
            for piece in new_pieces:
                if piece in _CORNER_HEXES[self.colour]:
                    actions[i][1] += 1*_DEFAULT_WEIGHTS["_IN_CORNER"]

            # how many in danger
            for qr in new_pieces:
                num_ally = 0
                num_enenmy = 0
                for step_q, step_r in _HEX_STEPS:
                    next_qr = qr[0] + step_q, qr[1] + step_r
                    if next_qr in self.hexes and self.board[next_qr] != ' ':
                        if self.board[next_qr] == self.colour:
                            num_ally += 1
                        else:
                            num_enenmy += 1
                actions[i][1] += _DEFAULT_WEIGHTS["_CLOSE_HEXES"] * (num_ally - num_enenmy)
            
            # moving towards to the end?
            actions[i][1] += (len(new_pieces)*6 - sum(self._exit_dist(qr)/2 for qr in new_pieces)) * (_DEFAULT_WEIGHTS["_CLOSE_END"] - adjust_weight)

            # keep repeat the same action?
            if temp_player.history[temp_player._snap()] >= 2:
                action[i][1] -= temp_player.history[temp_player._snap()] * _DEFAULT_WEIGHTS["_STAY_TOO_LONG"]
        return [action for action, value in sorted(actions, key=lambda x:x[1])]
  
    def maxn_search(self, depth):
        action_list = self.sort_action()
        self_colour = self.colour
        move = self.choose_action()
        value = {}
        for col in _COLOUR:
            if col != self_colour:
                temp_player = self.copy()
                temp_player.colour = col
                value[col] = temp_player.utility_score()
        value[self_colour] = self.utility_score()

        if depth == 1:
            return move, value

        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == 'PASS':
                #  or atype == 'EXIT':
                return (atype, ahexes), value

            player_cp = self.copy()
            player_cp.update(self_colour, (atype, ahexes))

            #immediate pruning
            if player_cp.utility_score() == _REWARDS["_WIN"]:
                value[self_colour] = player_cp.utility_score
                return (atype, ahexes), value

            for col in _COLOUR:
                if col != self_colour:
                    opponent = self.copy()
                    opponent.colour = col
                    reply_action, scores = opponent.maxn_search(depth-1)
                    if value[self_colour] < scores[self_colour]:
                        value = scores.copy()
                        move = (atype, ahexes)
        return move, value

    def copy(self):
        player_cp = MaxNPlayer(self.colour, depth=1)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        player_cp.opponents = self.opponents.copy()
        return player_cp

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
            elif self.history[curr_state] >= 4 or self.nturns >= _MAX_TURNS * 3:
                self.QL.saveTable(colour) 
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
        with open("qTable" +  ".json", 'r') as f:
            self.qTable = json.load(f)

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

    def saveTable(self, colour):
        #print(self.qTable)
        # TODO: Save the qTable into a json file
        with open('qTable' + '.json', 'w') as f:
            json.dump(self.qTable, f)