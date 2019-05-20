class MaxNPlayer(AbstractPlayer):
    def __init__(self, colour, depth=3):
        super().__init__(colour)
        self.opponents = {}
        self.eGreedy = eGreedy
        for col in _COLOUR:
            if col != self.colour and depth != 1:
                self.opponents[col] = MaxNPlayer(col, depth-1)
                
        self.QL = QLearningTable(colour, eGreedy=eGreedy)
        self.last_action = []
        self.last_state = None
        self.last_state_val = 0
        self.eGreedy = eGreedy
        self.keep_learning = True

        
    def action(self):
        if len(self._get_hexes()) == 0:
            return ("PASS", None)

        state = self._snap()
        self.QL.checkState(state, self._available_actions())
        if self.nturns >= 3 and self.last_action[0] != "PASS":
            reward = sigmoid(self.state_eval() - self.last_state_val)*10
            self.QL.learn(self.last_state, self.last_action, state, reward)

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
        super().update(colour, action)

        state = self._snap()
        self.nturns += 1
        self.history[state] += 1
        reward = 0
        with open("counter" +  ".json", 'r') as f:
            counter = json.load(f)
        
        # game not end but lost already
        if self.keep_learning:
            if len(self._get_hexes()) == 0 and self.scores[self.colour] < 4:
                reward = _REWARDS["_LOSE"]
                
                self.QL.learn(self.last_state, self.last_action, state, reward, True)
                self.QL.saveTable(colour) 
                self.keep_learning = False

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
                        self.QL.learn(self.last_state, self.last_action, state, reward, True)
                        self.QL.saveTable(colour) 
                        self.keep_learning = False
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
                self.QL.learn(self.last_state, self.last_action, state, reward, True)
                self.QL.saveTable(colour) 
                self.keep_learning = False
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

        # else
        # find top 4 pieces
        sorted_pieces = sorted([(qr, self._exit_dist(qr)) for qr in pieces], key=lambda x: x[1])[:5]

        # relatively close to each other
        # how many are in danger
        for qr, dist in sorted_pieces:
            danger = True
            for step_q, step_r in _HEX_STEPS:
                next_qr = qr[0] + step_q, qr[1] + step_r
                if next_qr in pieces:
                    danger = False
                    break
            if danger:
                value -= _DEFAULT_WEIGHTS["_CLOSE_HEXES"]

        # if (num_pieces > 0):
        #     for piece in sorted_pieces:
        #         value += sum(math.sqrt(math.pow(piece[0][0] - qr[0][0], 2) + math.pow(piece[0][1] - qr[0][1], 2)) for qr in sorted_pieces) * _DEFAULT_WEIGHTS["_CLOSE_HEXES"]
        #     value /= len(sorted_pieces)

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

        return sigmoid(value)*10

    def utility_score(self):
        value = 0
        for opponent, model in self.opponents.items():
            value += self.state_eval() - model.state_eval()
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

    def copy(self):
        player_cp = MaxNPlayer(self.colour, self.eGreedy)
        player_cp.hexes = self.hexes.copy()
        player_cp.board = self.board.copy()
        player_cp.scores = self.scores.copy()
        player_cp.opponents = self.opponents.copy()
        return player_cp