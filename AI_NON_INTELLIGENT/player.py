from search import Board, State, HEX_STEPS, h, h_state
import random
import json


_START = {'red': {(-3, 0), (-3, 1), (-3, 2), (-3, 3)}, 
    'green': {(0, -3), (1, -3), (2, -3), (3, -3)}, 
    'blue': {(3, 0), (2, 1), (1, 2), (0, 3)}}

_COLOUR = ['red', 'green', 'blue']

def find_jump_over_hex(hexes):
    for x_step, y_step in HEX_STEPS:
        hex = hexes[0][0]+x_step, hexes[0][1]+y_step
        check_hex = hex[0]+x_step, hex[1]+y_step
        if check_hex == hexes[1]:
            return hex

MAX_H_VALUE = 999
EAT_REWARD_WEIGHT = 10
EATEN_PUNISHMENT_WEIGHT = 1

class RandomPlayer:

    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the 
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your 
        program will play as (Red, Green or Blue). The value will be one of the 
        strings "red", "green", or "blue" correspondingly.
        """

        START = {'red': {(-3, 0), (-3, 1), (-3, 2), (-3, 3)}, 
            'green': {(0, -3), (1, -3), (2, -3), (3, -3)}, 
            'blue': {(3, 0), (2, 1), (1, 2), (0, 3)}}

        blocks = []
        for c, hexes in START.items():
            if c != colour:
                for i in hexes:
                    blocks.append(i)
        
        board = Board(colour, blocks)
        self.state = State(START[colour], board)

    def action(self):
        """
        This method is called at the beginning of each of your turns to request 
        a choice of action from your program.

        Based on the current state of the game, your player should select and 
        return an allowed action to play on this turn. If there are no allowed 
        actions, your player must return a pass instead. The action (or pass) 
        must be represented based on the above instructions for representing 
        actions.
        """
        # TODO: Decide what action to take.
        action_list = self.state._actions()
        index = int(random.random() * len(action_list))
        return action_list[index]


    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s 
        turns) to inform your player about the most recent action. You should 
        use this opportunity to maintain your internal representation of the 
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red", 
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or 
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action 
        (or pass) for the player colour (your method does not need to validate 
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        atype, ahexes = action
        if atype == "MOVE" or atype == "JUMP":
            src, dest = ahexes
            if (colour == self.state.board.colour):
                # check if it jumps over a enemey
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex not in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {jumped_over_hex})
                        self.state = State(self.state.piece_hexes - {src} | {dest} | {jumped_over_hex}, board)
                        return 
                # else
                self.state = State(self.state.piece_hexes - {src} | {dest}, self.state.board)
            else:
                # check if it jumps over an allay
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {jumped_over_hex} | {dest})
                        self.state = State(self.state.piece_hexes - {jumped_over_hex}, board)
                        return
                # else     
                board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {dest})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "EXIT":
            if (colour == self.state.board.colour):
                self.state = State(self.state.piece_hexes - {ahexes}, self.state.board)
            else:
                board = Board(self.state.board.colour, self.state.board.block_hexes - {ahexes})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "PASS":
            pass

class HPlayer:

    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the 
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your 
        program will play as (Red, Green or Blue). The value will be one of the 
        strings "red", "green", or "blue" correspondingly.
        """

        START = {'red': {(-3, 0), (-3, 1), (-3, 2), (-3, 3)}, 
            'green': {(0, -3), (1, -3), (2, -3), (3, -3)}, 
            'blue': {(3, 0), (2, 1), (1, 2), (0, 3)}}

        blocks = []
        for c, hexes in START.items():
            if c != colour:
                for i in hexes:
                    blocks.append(i)
        
        board = Board(colour, blocks)
        self.state = State(START[colour], board)

    def action(self):
        """
        This method is called at the beginning of each of your turns to request 
        a choice of action from your program.

        Based on the current state of the game, your player should select and 
        return an allowed action to play on this turn. If there are no allowed 
        actions, your player must return a pass instead. The action (or pass) 
        must be represented based on the above instructions for representing 
        actions.
        """
        # TODO: Decide what action to take.
        action_list = self.state._actions()

        min_h = 999
        final_action = None
        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == "PASS" or atype == "EXIT":
                return action_list[0]

            src, dest = ahexes
            temp_state = State(self.state.piece_hexes, self.state.board)
            temp_player = HPlayer(self.state.board.colour)
            temp_player.state = temp_state
            temp_player.update(self.state.board.colour, (atype, ahexes))

            h_value = h(temp_player.state)
            if h_value < min_h:
                min_h = h_value
                final_action = (atype, ahexes)
        return final_action


    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s 
        turns) to inform your player about the most recent action. You should 
        use this opportunity to maintain your internal representation of the 
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red", 
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or 
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action 
        (or pass) for the player colour (your method does not need to validate 
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        atype, ahexes = action
        if atype == "MOVE" or atype == "JUMP":
            src, dest = ahexes
            if (colour == self.state.board.colour):
                # check if it jumps over a enemey
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex not in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {jumped_over_hex})
                        self.state = State(self.state.piece_hexes - {src} | {dest} | {jumped_over_hex}, board)
                        return 
                # else
                self.state = State(self.state.piece_hexes - {src} | {dest}, self.state.board)
            else:
                # check if it jumps over an allay
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {jumped_over_hex} | {dest})
                        self.state = State(self.state.piece_hexes - {jumped_over_hex}, board)
                        return
                # else     
                board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {dest})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "EXIT":
            if (colour == self.state.board.colour):
                self.state = State(self.state.piece_hexes - {ahexes}, self.state.board)
            else:
                board = Board(self.state.board.colour, self.state.board.block_hexes - {ahexes})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "PASS":
            pass

class ImprovedHPlayer:

    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the 
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your 
        program will play as (Red, Green or Blue). The value will be one of the 
        strings "red", "green", or "blue" correspondingly.
        """

        self.finished = 0

        START = {'red': {(-3, 0), (-3, 1), (-3, 2), (-3, 3)}, 
            'green': {(0, -3), (1, -3), (2, -3), (3, -3)}, 
            'blue': {(3, 0), (2, 1), (1, 2), (0, 3)}}

        blocks = []
        for c, hexes in START.items():
            if c != colour:
                for i in hexes:
                    blocks.append(i)
        
        board = Board(colour, blocks)
        self.state = State(START[colour], board)
        self.colour = colour

    def action(self):
        """
        This method is called at the beginning of each of your turns to request 
        a choice of action from your program.

        Based on the current state of the game, your player should select and 
        return an allowed action to play on this turn. If there are no allowed 
        actions, your player must return a pass instead. The action (or pass) 
        must be represented based on the above instructions for representing 
        actions.
        """
        # TODO: Decide what action to take.
        action_list = self.state._actions()

        min_h = MAX_H_VALUE
        final_action = None
        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == 'PASS' or atype == 'EXIT':
                return (atype, ahexes)

            # check if it eats any enemy
            temp_state = State(self.state.piece_hexes, self.state.board)
            last_num_hexes = len(temp_state.piece_hexes) + self.finished
            temp_player = ImprovedHPlayer(self.state.board.colour)
            temp_player.state = temp_state
            temp_player.update(self.state.board.colour, (atype, ahexes))
            new_num_hexes = len(temp_player.state.piece_hexes) + temp_player.finished
            reward = new_num_hexes - last_num_hexes

            # check if any ally may be eaten
            src, dest = ahexes
            punishment = 0
            for i in range(1, 3):
                for x_step, y_step in HEX_STEPS:
                    neighbour = dest[0] + x_step*i, dest[1] + y_step*i
                    if neighbour in temp_player.state.board and self.state.board.is_blocked(neighbour):
                        punishment += 1/i

            h_value = h(temp_player.state) - EAT_REWARD_WEIGHT*reward + punishment
            if h_value < min_h:
                min_h = h_value
                final_action = (atype, ahexes)
        return final_action


    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s 
        turns) to inform your player about the most recent action. You should 
        use this opportunity to maintain your internal representation of the 
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red", 
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or 
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action 
        (or pass) for the player colour (your method does not need to validate 
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        atype, ahexes = action
        if atype == 'MOVE' or atype == 'JUMP':
            src, dest = ahexes
            if (colour == self.state.board.colour):
                # check if it jumps over a enemey
                if atype == 'JUMP':
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex not in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {jumped_over_hex})
                        self.state = State(self.state.piece_hexes - {src} | {dest} | {jumped_over_hex}, board)
                        return 
                # else
                self.state = State(self.state.piece_hexes - {src} | {dest}, self.state.board)
            else:
                # check if it jumps over an allay
                if atype == 'JUMP':
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {jumped_over_hex} | {dest})
                        self.state = State(self.state.piece_hexes - {jumped_over_hex}, board)
                        return
                # else     
                board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {dest})
                self.state = State(self.state.piece_hexes, board)
        elif atype == 'EXIT':
            if (colour == self.state.board.colour):
                self.finished += 1
                self.state = State(self.state.piece_hexes - {ahexes}, self.state.board)
            else:
                board = Board(self.state.board.colour, self.state.board.block_hexes - {ahexes})
                self.state = State(self.state.piece_hexes, board)
        elif atype == 'PASS':
            pass

class MaxNPlayer:

    def __init__(self, colour, create=True):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the 
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your 
        program will play as (Red, Green or Blue). The value will be one of the 
        strings "red", "green", or "blue" correspondingly.
        """

        # self.error = 1
        self.opponents = {}

        blocks = []
        for col, piece in _START.items():
            if col != colour:
                for p in piece:
                    blocks.append(p)
        board = Board(colour, blocks)
        self.state = State(_START[colour], board)

        for col in _COLOUR:
            if col != colour and create:
                self.opponents[col] = MaxNPlayer(col, False)

    def action(self):
        """
        This method is called at the beginning of each of your turns to request 
        a choice of action from your program.

        Based on the current state of the game, your player should select and 
        return an allowed action to play on this turn. If there are no allowed 
        actions, your player must return a pass instead. The action (or pass) 
        must be represented based on the above instructions for representing 
        actions.
        """
        # TODO: Decide what action to take.
        return self.depthSearch(3)[0]

    def update(self, colour, action, keep=True):
        """
        This method is called at the end of every turn (including your player’s 
        turns) to inform your player about the most recent action. You should 
        use this opportunity to maintain your internal representation of the 
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red", 
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or 
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action 
        (or pass) for the player colour (your method does not need to validate 
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        atype, ahexes = action
        if atype == 'MOVE' or atype == 'JUMP':
            src, dest = ahexes
            if (colour == self.state.board.colour):
                # check if it jumps over a enemey
                if atype == 'JUMP':
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex not in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {jumped_over_hex})
                        self.state = State(self.state.piece_hexes - {src} | {dest} | {jumped_over_hex}, board)
                        return 
                # else
                self.state = State(self.state.piece_hexes - {src} | {dest}, self.state.board)
            else:
                # check if it jumps over an allay
                if atype == 'JUMP':
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {jumped_over_hex} | {dest})
                        self.state = State(self.state.piece_hexes - {jumped_over_hex}, board)
                        return
                # else     
                board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {dest})
                self.state = State(self.state.piece_hexes, board)
        elif atype == 'EXIT':
            if (colour == self.state.board.colour):
                self.state = State(self.state.piece_hexes - {ahexes}, self.state.board)
            else:
                board = Board(self.state.board.colour, self.state.board.block_hexes - {ahexes})
                self.state = State(self.state.piece_hexes, board)
        elif atype == 'PASS':
            return

        for opponent, model in self.opponents.items():
            model.update(colour, action, False)

    def copy(self):

        player_cp = MaxNPlayer(self.state.board.colour)
        player_cp.state = State(self.state.piece_hexes, self.state.board)

        for col in _COLOUR:
            if col != self.state.board.colour:
                opponent_state = self.opponents[col].state
                player_cp.opponents[col] = MaxNPlayer(col)
                player_cp.opponents[col].state = State(opponent_state.piece_hexes, opponent_state.board)

        return player_cp

    def depthSearch(self, depth):
        if depth == 1:
            score = {}
            for col in _COLOUR:
                if col != self.state.board.colour:
                    score[col] = h_state(self.opponents[col].state)
            score[self.state.board.colour] = h_state(self.state)
            return self.choose_action(), score
        
        action_list = self.state._actions()
        move = self.choose_action()
        value = {}
        for col in _COLOUR:
            if col != self.state.board.colour:
                value[col] = h_state(self.opponents[col].state)
        value[self.state.board.colour] = h_state(self.state)

        for atype, ahexes in action_list:
            # if pass, return directly
            if atype == 'PASS':
                #  or atype == 'EXIT':
                return (atype, ahexes), value

            player_cp = self.copy()
            player_cp.update(player_cp.state.board.colour, (atype, ahexes))
            player_colour = player_cp.state.board.colour
            
            # if atype == 'EXIT':
            #     value[player_colour] = h_state(player_cp.state)
            #     return 

            for col in _COLOUR:
                if col != player_colour and len(player_cp.opponents[col].state.piece_hexes)>0:
                    reply_action, scores = player_cp.opponents[col].depthSearch(depth-1)
                    if player_colour not in value.keys() or value[player_colour] < scores[player_colour]:
                        value = scores.copy()
                        move = (atype, ahexes)
        # if move is None:
        #     move = action_list[0]
        return move, value

    # def choose_action(self):
    #     """
    #     This method is called at the beginning of each of your turns to request 
    #     a choice of action from your program.

    #     Based on the current state of the game, your player should select and 
    #     return an allowed action to play on this turn. If there are no allowed 
    #     actions, your player must return a pass instead. The action (or pass) 
    #     must be represented based on the above instructions for representing 
    #     actions.
    #     """
    #     # TODO: Decide what action to take.
    #     action_list = self.state._actions()

    #     min_h = MAX_H_VALUE
    #     final_action = None
    #     for atype, ahexes in action_list:
    #         # if pass, return directly
    #         if atype == 'PASS' or atype == 'EXIT':
    #             return (atype, ahexes)

    #         # check if it eats any enemy
    #         temp_state = State(self.state.piece_hexes, self.state.board)
    #         last_num_hexes = len(temp_state.piece_hexes)
    #         temp_player = ImprovedHPlayer(self.state.board.colour)
    #         temp_player.state = temp_state
    #         temp_player.update(self.state.board.colour, (atype, ahexes))
    #         new_num_hexes = len(temp_player.state.piece_hexes)
    #         reward = new_num_hexes - last_num_hexes

    #         # check if any ally may be eaten
    #         src, dest = ahexes
    #         punishment = 0
    #         for i in range(1, 3):
    #             for x_step, y_step in HEX_STEPS:
    #                 neighbour = dest[0] + x_step*i, dest[1] + y_step*i
    #                 if neighbour in temp_player.state.board and self.state.board.is_blocked(neighbour):
    #                     punishment += 1/i

    #         h_value = h(temp_player.state) - EAT_REWARD_WEIGHT*reward + punishment
    #         if h_value < min_h:
    #             min_h = h_value
    #             final_action = (atype, ahexes)
    #     return final_action
    def choose_action(self):
                # TODO: Decide what action to take.
        action_list = self.state._actions()

        value = 0
        final_action = None
        for atype, ahexes in action_list:
            # if pass, return directly
            # or atype == "EXIT"
            if atype == "PASS":
                return (atype, ahexes)

            src, dest = ahexes
            temp_state = State(self.state.piece_hexes, self.state.board)
            temp_player = HPlayer(self.state.board.colour)
            temp_player.state = temp_state
            temp_player.update(self.state.board.colour, (atype, ahexes))

            h_value = h_state(temp_player.state, self.state)
            if h_value > value:
                value = h_value
                final_action = (atype, ahexes)
        
        # if final_action is None:
        #     final_action = action_list[0]
        return final_action

class QLearningPlayer:

    def __init__(self, colour):
        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your
        program will play as (Red, Green or Blue). The value will be one of the
        strings "red", "green", or "blue" correspondingly.
        """

        START = {'red': {(-3, 0), (-3, 1), (-3, 2), (-3, 3)},
                 'green': {(0, -3), (1, -3), (2, -3), (3, -3)},
                 'blue': {(3, 0), (2, 1), (1, 2), (0, 3)}}

        blocks = []
        for c, hexes in START.items():
            if c != colour:
                for i in hexes:
                    blocks.append(i)

        board = Board(colour, blocks)
        self.state = State(frozenset(START[colour]), board)
        # create the table for Q-Learning
        self.QL = QLearningTable()
        # recording of the state and number of turns used to check whether the game draw
        # self.drawsign = False
        self.history = {}
        self.nturns = 0
        # recording of the scores every player get used to check the winner
        self.score = {'red': 0, 'green': 0, 'blue': 0}
        # + hash(self.state.board.block_hexes)


    def action(self):
        """
        This method is called at the beginning of each of your turns to request
        a choice of action from your program.

        Based on the current state of the game, your player should select and
        return an allowed action to play on this turn. If there are no allowed
        actions, your player must return a pass instead. The action (or pass)
        must be represented based on the above instructions for representing
        actions.
        """
        # TODO: Decide what action to take.
        #action_list = self.state._actions()

        reward = 0
        self.QL.checkState(self.state)

        #atype, ahexes = self._action
        if self.nturns >= 3 and self._action[0] != "PASS":
            reward = self.calcReward()
            temp__state = State(self._state.piece_hexes, self._state.board)
            self.QL.learn(temp__state, self._action, self.state, reward)

        self._state = State(self.state.piece_hexes, self.state.board)

        self._action = self.QL.chooseAction(self.state)
        return self._action


        # index = int(random.random() * len(action_list))
        # return action_list[index]

    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s
        turns) to inform your player about the most recent action. You should
        use this opportunity to maintain your internal representation of the
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red",
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action
        (or pass) for the player colour (your method does not need to validate
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        atype, ahexes = action
        if atype == "MOVE" or atype == "JUMP":
            src, dest = ahexes
            if (colour == self.state.board.colour):
                # check if it jumps over a enemey
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex not in self.state.piece_hexes:
                        board = Board(self.state.board.colour, self.state.board.block_hexes - {jumped_over_hex})
                        self.state = State(self.state.piece_hexes - {src} | {dest} | {jumped_over_hex}, board)

                        #return
                        # else
                self.state = State(self.state.piece_hexes - {src} | {dest}, self.state.board)
            else:
                # check if it jumps over an allay
                if atype == "JUMP":
                    jumped_over_hex = find_jump_over_hex(ahexes)
                    if jumped_over_hex in self.state.piece_hexes:
                        board = Board(self.state.board.colour,
                                      self.state.board.block_hexes - {src} | {jumped_over_hex} | {dest})
                        self.state = State(self.state.piece_hexes - {jumped_over_hex}, board)

                        #return
                # else
                board = Board(self.state.board.colour, self.state.board.block_hexes - {src} | {dest})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "EXIT":
            self.score[colour] += 1
            if (colour == self.state.board.colour):
                self.state = State(self.state.piece_hexes - {ahexes}, self.state.board)
            else:
                board = Board(self.state.board.colour, self.state.board.block_hexes - {ahexes})
                self.state = State(self.state.piece_hexes, board)
        elif atype == "PASS":
            pass

        #print("updateeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")
        #print(self.state.piece_hexes)
        #print(self.state.__hash__() + hash(frozenset(self.state.board.block_hexes)))
        self.nturns += 1
        if str(self.state.__hash__()) + str(hash(frozenset(self.state.board.block_hexes))) not in self.history:
            self.history[str(self.state.__hash__()) + str(hash(frozenset(self.state.board.block_hexes)))] = 1
        else:
            self.history[str(self.state.__hash__()) + str(hash(frozenset(self.state.board.block_hexes)))] += 1

        if self.nturns >= 256 * 3 or max(self.history.values()) >= 4 * 3:
            #self.drawsign = True
            #print("drawwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww")
            reward = 0
            if self._action[0] != "PASS":
                self.QL.learn(self._state, self._action, self.state, reward, True)
            self.QL.saveTable()
            with open('winner.txt', 'a') as f:
                f.write("drawwwwwwwwwwwwwwwwwwwwwww\n")
        if max(self.score.values()) >= 4:
            #print("winnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnn")
            if self.score[self.state.board.colour] >= 4:
                reward = 100
                with open('winner.txt', 'a') as f:
                    f.write("winnnnnnnnnnnnnnnnnnnnnnnn\n")
            else:
                reward = -100
                with open('winner.txt', 'a') as f:
                    f.write("loseeeeeeeeeeeeeeeeeeeeeee\n")

            if self._action[0] != "PASS":
                self.QL.learn(self._state, self._action, self.state, reward, True)
            self.QL.saveTable()
        #print("updateeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee")

    def calcReward(self):

        distReward = self.calcDist(self.state) - self.calcDist(self._state)
        if self._action[0] == "EXIT":
            exitReward = 10
            pieceReward = len(self.state.piece_hexes) - len(self._state.piece_hexes)
        else:
            exitReward = 0
            pieceReward = len(self.state.piece_hexes) - len(self._state.piece_hexes)

        return distReward + exitReward + pieceReward

    def calcDist(self, state):
        hexes = state.piece_hexes
        dist = state.board.exit_dist
        return sum(dist(qr) for qr in hexes)

class QLearningTable:

    def __init__(self, learningRate = 0.1, rewardDecay = 0.9, eGreedy = 0.6):

        # learningRate is the coefficient of the result we add to the previous value every time
        self.learningRate = learningRate
        # rewardDecay is the coefficient of the difference
        self.rewardDecay = rewardDecay
        # eGreedy means it has an eGreedy probability to choose the action based on the qTable
        self.eGreedy = eGreedy
        with open("qTable.json", 'r') as f:
            self.qTable = json.load(f)
        #print(self.qTable)
        #print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
    def chooseAction(self, state):
        # TODO: Decide what action to take based on the qTable
        if max(self.qTable[str(state.__hash__())+ str(hash(frozenset(state.board.block_hexes)))].values()) == 0 or random.random() > self.eGreedy:
            #random
            action_list = state._actions()
            return action_list[int(random.random() * len(action_list))]

        else:
            actions = self.qTable[str(state.__hash__()) + str(hash(frozenset(state.board.block_hexes)))]

            maxValue = -1000
            bestAction = None
            #(actions)
            for key, value in actions.items():
                if (value > maxValue):
                    maxValue = value
                    bestAction = eval(key)

            #bestAction = eval(max(actions.items(), key=lambda x: x))

            #print(bestAction)
            #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            return bestAction

    def checkState(self, state):
        # TODO: Check if the state is in the qTable and add it if not
        if str(state.__hash__()) + str(hash(frozenset(state.board.block_hexes))) not in self.qTable:
            self.qTable[str(state.__hash__()) + str(hash(frozenset(state.board.block_hexes)))] = {}
            for action in state._actions():
                self.qTable[str(state.__hash__()) + str(hash(frozenset(state.board.block_hexes)))][str(action)] = 0
                #print(action)
        else:
            #print("appear")
            pass



    def learn(self, _state, action, state, reward, end=False):
        # end = False ?
        # TODO: Update the qTable based on the result of the action using the Q-Learning algorithm
        #print("*******learn********")
        if not end:
            qTarget = reward + self.rewardDecay*max(self.qTable[str(state.__hash__()) + str(hash(frozenset(state.board.block_hexes)))].values())
            #print(self.qTable)
            #print(self.qTable[repr(_state)])
            #print(self.qTable)
            #if len(self.qTable[_state]) != len(_state._actions()):
            qPredict = self.qTable[str(_state.__hash__()) + str(hash(frozenset(_state.board.block_hexes)))][str(action)]

        else:
            qTarget = reward
            #print(self.qTable[str(_state.__hash__()) + str(hash(frozenset(_state.board.block_hexes)))])
            qPredict = self.qTable[str(_state.__hash__()) + str(hash(frozenset(_state.board.block_hexes)))][str(action)]
        self.qTable[str(_state.__hash__()) + str(hash(frozenset(_state.board.block_hexes)))][str(action)] += self.learningRate * (qTarget - qPredict)

    def saveTable(self):
        #print(self.qTable)
        # TODO: Save the qTable into a json file
        # with open('qTable.json', 'w') as f:
        #     string = json.dumps(self.qTable)
        #     f.write(string)
        with open('qTable.json', 'w') as f:
            # for key, value in self.qTable.items():
            #     f.write(key)
            json.dump(self.qTable, f)
                #f.write(value)