from referee.game import *
from AI_NON_INTELLIGENT.player_new import *
from AI_NON_INTELLIGENT.player import ImprovedHPlayer
import numpy as np

i = 0
n = 0
learningRate = 0.1
rewardDecay = 0.9
eGreedy = 1
eGreedy_decay = 0.01

def play(players):
    # Set up a new Chexers game and initialise a Red, Green and Blue player
    # (constructing three Player classes including running their .__init__() 
    # methods).
    game = Chexers(debugboard=True)

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

with open("counter" +  ".json", 'w') as f:
    json.dump({}, f)
result = {'r': 0,
          'b': 0,
          'g': 0}
while i < 10:
    #print(i)
    i += 1
    n += 1
    #if n < 100:
    players = (QLearningPlayer("red", eGreedy=eGreedy), GreedyPlayer('green'), ImprovedHPlayer('blue'))

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

    eGreedy = 0.01 + (1-0.01)*np.exp(-0.00005*i)
    # else:
    #     players = (QLearningPlayer("red", learningRate, rewardDecay, eGreedy), GreedyPlayer('green'), RandomPlayer("blue"))
    #     play(players)
    #     eGreedy = 0.01 + (1-0.01)*np.exp(-0.00005*i)
    
    # n += 1
print(i + ": " + result)