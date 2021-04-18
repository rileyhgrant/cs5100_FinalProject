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
               first='OffensiveReflexAgent', second='OffensiveReflexAgent'):
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
        agentState = gameState.getAgentState(self.index)

        # just move towards closest food while in base
        if not agentState.isPacman:
            currentPos = gameState.getAgentPosition(self.index)
            foodList = self.getFood(gameState).asList()
            closestFoodPos = None
            minFoodDist = 1000000
            for foodPos in foodList:
                foodDist = self.getMazeDistance(currentPos, foodPos)
                if foodDist < minFoodDist:
                    minFoodDist = foodDist
                    closestFoodPos = foodPos

            chosenAction = None
            minDist = 1000000
            actions = gameState.getLegalActions(self.index)
            for action in actions:
                nextPos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
                dist = self.getMazeDistance(nextPos, closestFoodPos)
                if dist < minDist:
                    minDist = dist
                    chosenAction = action

        # if on enemy's side, do MCTS
        else:
            visibleIndices = self.getVisibleEnemyIndices(gameState)
            visibleIndices.insert(0, self.index) #add teammates or no?

            root = MCNode(gameState, None, None, self.index, visibleIndices)
            chosenAction = MCTS(root)


        return chosenAction

        # have if statements to override the monte-carlo's choice
        """
        def evaluate(MCNode):
            features = self.getFeatures(gameState, action)
            weights = self.getWeights(gameState, action)
            return features * weights

        mctsNode = MCTS( MCNode( gameState, self.index, None, evaluate))
        return mctsNode.action
        #return random.choice(actions)
        """

    def getVisibleEnemyIndices(self, gameState):
        if gameState.isOnRedTeam(self.index):
            enemyIndices = gameState.getBlueTeamIndices()
        else:
            enemyIndices = gameState.getRedTeamIndices()

        visibleEnemyIndices = list()
        for enemyIndex in enemyIndices:
            if gameState.getAgentPosition(enemyIndex) is not None:
                visibleEnemyIndices.append(enemyIndex)

        return visibleEnemyIndices


class DefensiveReflexAgent(ReflexCaptureAgent):

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        # have if statements to override the monte-carlo's choice
        def evaluate(MCNode):
            features = self.getFeatures(gameState, action)
            weights = self.getWeights(gameState, action)
            return features * weights

        mctsNode = MCTS(MCNode(gameState, self.index, None, evaluate))
        return mctsNode.action
        # return random.choice(actions)


# https://www.geeksforgeeks.org/ml-monte-carlo-tree-search-mcts/
# https://medium.com/@quasimik/implementing-monte-carlo-tree-search-in-node-js-5f07595104df
'''
Class to represent the Monte Carlo Tree Node and its children
'''


class MCNode():
    def __init__(self, gameState, parent, action, index, visibleAgentIndices):
        # self.numWins = 0
        self.avgScore = 0.0
        self.numGames = 0
        self.gameState = gameState
        self.parent = parent
        self.children = list()  # list of MCNodes
        # self.isEnemy = False
        self.index = index
        self.action = action
        # self.evaluate = evaluate
        self.visibleAgentIndices = visibleAgentIndices

    def isFullyExpanded(self):
        if len(self.children) == 0:  # added
            return False  # added

        for child in self.children:
            if not child.visited():
                return False

        return True

    def visited(self):
        return self.numGames > 0

    def getNodeWithBestUCT(self):
        #nextIndex = (self.index + 1) % 4
        #isInvisible = self.gameState.getAgentPosition( nextIndex ) is None
        #if isInvisible:
        #    return None

        chosenNode = None
        maxUCT = -1000000
        for child in self.children:
            if child.getUCT() > maxUCT:
                maxUCT = child.getUCT()
                chosenNode = child

        return chosenNode

    def getUCT(self):
        exploreParam = math.sqrt(2)
        # TODO: how to use avgScore instead of numWins in this formula
        return self.avgScore * self.numGames + exploreParam * math.sqrt(math.log(self.parent.numGames) / self.numGames)

    def hasChildren(self):
        return len(self.children) != 0

    def getUnusedActions(self):
        actions = self.gameState.getLegalActions(self.index)
        for child in self.children:
            if child.action in actions:
                actions.remove(child.action)

        return actions

    def generateSuccessor(self):
        #if self.isFullyExpanded():
        #    print("Program shouldn't reach here")
        #    return random.choice(self.children)
        #else:
        #print("index is: ", self.index)
        #print("gameState is: ", self.gameState)
        #print("indices are: ", self.gameState.getRedTeamIndices(), self.gameState.getBlueTeamIndices())
        
        #if self.gameState.getAgentPosition( self.index ) is None:
        #    action = Directions.STOP
        #    print("Program ran here.")
        #else:
        actions = self.gameState.getLegalActions(self.index)
        action = random.choice(actions)

        nextState = self.gameState.generateSuccessor(self.index, action)
        #newIndex = (self.index + 1) % 4
        newIndex = self.getNextAgentIndex()
        successor = MCNode(nextState, self, action, newIndex, self.visibleAgentIndices)

            # while not self.children.__contains__(successor):
            #    action = random.choice(self.gameState.getLegalActions(self.index))
            #    nextState = self.gameState.generateSuccessor(self.index, action)
            #    successor = MCNode(nextState, nextState.getIndex(), action)
        return successor
    
    def getNextAgentIndex(self):
        listIndex = self.visibleAgentIndices.index(self.index)
        listIndex = (listIndex + 1) % len(self.visibleAgentIndices)
        nextAgentIndex = self.visibleAgentIndices[listIndex]
        return nextAgentIndex



def MCTS(node):
    start = time.time()
    while 1 > (time.time() - start):  # modified
        leaf = search(node)
        #if leaf is None:
            # TODO continue search? move towards closest dot?
            #print("Leaf is None")
        #    return random.choice(node.gameState.getLegalActions(node.index))
        simNode = expand(leaf)
        resultScore = rollout(simNode)
        backpropagate(simNode, resultScore)

    bestChild = best_child(node)
    print("BEST ACTION IS: ", bestChild.action)
    return bestChild.action
    # return None


def best_child(node):
    isRed = node.gameState.isOnRedTeam( node.index )


    # maxWinrate = 0
    maxVisits = -1000000  # added
    bestChild = None
    for child in node.children:
        # winrate = child.numWins / child.numGames
        # if winrate > maxWinrate:
        #    maxWinrate = winrate
        #    bestChild = child

        if child.numGames > maxVisits:  # added
            maxVisits = child.numGames  # added
            bestChild = child  # added

    #print( "\n===============")
    #print( "RETURNING BEST CHILD: ",  bestChild, "\n")
    return bestChild


def search(node):
    currentNode = node
    #while currentNode is not None and currentNode.isFullyExpanded():
    while currentNode.isFullyExpanded():
        currentNode = currentNode.getNodeWithBestUCT()


    return currentNode


def expand(node):  # added
    #print(node.gameState.getAgentState(node.index))
    actions = node.getUnusedActions()
    #print(actions)
    chosenAction = random.choice(actions)
    nextState = node.gameState.generateSuccessor(node.index, chosenAction)

    #newIndex = ( node.index + 1 ) % 4
    newIndex = node.getNextAgentIndex()
    chosenChild = MCNode(nextState, node, chosenAction, newIndex, node.visibleAgentIndices)
    node.children.append(chosenChild)

    return chosenChild


# keep choosing random actions until an end state is reached
def rollout(node):
    # potentially add depth parameter if time is an issue
    currentNode = node
    for i in range(100):
        currentNode = rollout_policy(currentNode)
        
    #while not currentNode.isTerminal():
    #    currentNode = rollout_policy(currentNode)
    
    """
    terminal = False
    pelletEaten = False
    while not terminal:
        firstAgentIndex = currentNode.visibleAgentIndices[0]
        if currentNode.index == firstAgentIndex:
            prevPellets = currentNode.gameState.getAgentState(firstAgentIndex).numCarrying
            currentNode = rollout_policy(currentNode)
            currPellets = currentNode.gameState.getAgentState(firstAgentIndex).numCarrying
            if currPellets - prevPellets == 1:
                terminal = True
                pelletEaten = True
        else:
            currentNode = rollout_policy(currentNode)
    if pelletEaten:
        return 1.0
    else:
        return 0.0
    """

    #return node.evaluate(currentNode)
    return currentNode.gameState.getScore()


def rollout_policy(node):
    #if node.gameState.getAgentPosition(node.index) is None:
    #    newNode = MCNode( node.gameState, node, Directions.STOP, (node.index + 1) % 4) # does the action matter?
    #    return newNode
    #else:
    return node.generateSuccessor()
    #return node.generateSuccessor()


#
def backpropagate(node, result):
    currentNode = node
    while currentNode is not None:
        currSum = currentNode.avgScore * currentNode.numGames
        newSum = currSum + result
        currentNode.numGames = currentNode.numGames + 1
        currentNode.avgScore = newSum / currentNode.numGames

        # set node to parent to keep looping
        currentNode = currentNode.parent
