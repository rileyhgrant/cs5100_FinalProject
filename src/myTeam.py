# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
import time
import math


#################
# Team    wip   #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):
    #  first='DummyAgent', second='DummyAgent'):
    """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########


class ReflexCaptureAgent(CaptureAgent):
    """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

    def registerInitialState(self, gameState):
        """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

        '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
        CaptureAgent.registerInitialState(self, gameState)

        '''
    Your initialization code goes here, if you need any.
    '''

    def chooseAction(self, gameState):
        """
    Picks among actions randomly.
    """
        actions = gameState.getLegalActions(self.index)

        '''
    You should change this in your own agent.
    '''
        return random.choice(actions)

    def evaluate(self, gameState, action):
        """
    Computes a linear combination of features and feature weights
    """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights


class OffensiveReflexAgent(ReflexCaptureAgent):

    def __init__(self, index):
        CaptureAgent.__init__(self, index)

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        # have if statements to override the monte-carlo's choice
        
        def evaluate(MCNode):
            features = self.getFeatures(gameState, action)
            weights = self.getWeights(gameState, action)
            return features * weights

        node = MCNode( gameState, self.index, None, evaluate)
        print( "offense ahhhh", node )
        mctsNode = MCTS( node )
        # mctsNode = MCTS( MCNode( gameState, self.index, None, evaluate))
        return mctsNode.action
        #return random.choice(actions)


class DefensiveReflexAgent(ReflexCaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        # have if statements to override the monte-carlo's choice
        def evaluate(MCNode):
            features = self.getFeatures(gameState, action)
            weights = self.getWeights(gameState, action)
            return features * weights

        node = MCNode(gameState, self.index, None, evaluate)
        print("defense ahhhh", node)
        mctsNode = MCTS(node)
        # mctsNode = MCTS( MCNode( gameState, self.index, None, evaluate))
        return mctsNode.action
        #return random.choice(actions)


# https://www.geeksforgeeks.org/ml-monte-carlo-tree-search-mcts/
# https://medium.com/@quasimik/implementing-monte-carlo-tree-search-in-node-js-5f07595104df
'''
Class to represent the Monte Carlo Tree Node and its children
'''


class MCNode():
    def __init__(self, gameState, index, action, evaluate):
        self.numWins = 0
        self.numGames = 0
        self.gameState = gameState
        self.parent = None
        self.children = list()  # list of MCNodes TODO: NEED TO ACTUALLY GIVE CHILDREN
        self.isEnemy = False
        self.index = index
        self.action = action
        self.evaluate = evaluate

    def isFullyExpanded(self):
        for child in self.children:
            if not child.visited():
                return False

        return True

    def visited(self):
        return self.numGames > 0

    def getNodeWithBestUCT(self):
        chosenNode = None
        maxUCT = -1000000
        # TODO: Problem is this bad larry has no children
        for child in self.children:
            if child.getUCT() > maxUCT:
                maxUCT = child.getUCT()
                chosenNode = child

        return chosenNode

    def getUCT(self):
        exploreParam = math.sqrt(2)
        return self.numWins / self.numGames + exploreParam * math.sqrt(math.log(self.parent.numGames) / self.numGames)

    def hasChildren(self):
        return len(self.children) != 0

    def generateSuccessor(self):
        if self.isFullyExpanded():
            return random.choice(self.children)
        else:
            gameState = self.gameState.generateSuccessor(self.index, Directions.STOP)
            successor = MCNode(gameState, gameState.getIndex(), Directions.STOP)
            while not self.children.__contains__(successor):
                action = random.choice(self.gameState.getLegalActions(self.index))
                gameState = self.gameState.generateSuccessor(self.index, action)
                successor = MCNode(gameState, gameState.getIndex(), action)
            return successor

    def type(self):
        return "mcnode"


def MCTS(MCNode):
    start = time.time()
    print( "line 211, MCNode: ", MCNode, MCNode.type() )
    while 3000 > (time.time() - start) * 1000:  # resources remaining (time) 3s
        leaf = search(MCNode)
        result = rollout(leaf)
        backpropagate(MCNode, result)

    return best_child(MCNode)


def best_child(MCNode):
    maxWinrate = 0
    bestChild = None
    for child in MCNode.children:
        winrate = child.numWins / child.numGames
        if winrate > maxWinrate:
            bestChild = child
    return bestChild



def search(MCNode):
    currentNode = MCNode
    print( "line 211, MCNode: ", MCNode, MCNode.type() )
    print( "line 211, currentNode: ", currentNode, currentNode.type() )
    while currentNode.isFullyExpanded():
        print( 'ran once' )
        currentNode = currentNode.getNodeWithBestUCT()
        print( currentNode )

    if currentNode.hasChildren():
        for child in currentNode.children:
            if not child.visited:
                return child
    else:
        return currentNode


# keep choosing random actions until an end state is reached
def rollout(MCNode):
    # potentially add depth parameter if time is an issue
    currentNode = MCNode
    while not currentNode.isTerminal():
        currentNode = rollout_policy(currentNode)
    return MCNode.evaluate(currentNode)


def rollout_policy(MCNode):
    return MCNode.generateSuccessor()


#
def backpropagate(MCNode, result):
    isEnemyWin = result < 0
    currentNode = MCNode
    while currentNode is not None:
        currentNode.numPlays += 1
        if (currentNode.isEnemy == isEnemyWin):
            currentNode.numWins += 1

        # set node to parent to keep looping
        currentNode = currentNode.parent
