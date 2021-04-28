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


# the offensive agent that used both MCTS and greedy algorithm
class OffensiveReflexAgent(ReflexCaptureAgent):

    # initialize agent
    def __init__(self, index):
        CaptureAgent.__init__(self, index)

    # initialize the state of the agent
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    # choose the optimal action
    def chooseAction(self, gameState):
        agentState = gameState.getAgentState(self.index)
        visibleIndices = self.getVisibleEnemyIndices(gameState)

        # just move towards closest food while in base
        # TODO: Could add a clause to if theres a ghost within ~3 tiles,
        #   chase it down?
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

            # get closest ghost, if they're within 3 units, chase them.
            #   if and ugly repetition to override above beeline to enemy side, iff theres a nearby enemy
            closestGhostPos = None
            closestGhostDist = 999999
            if len(visibleIndices) > 0:
                for enemyIndex in visibleIndices:
                    currEnemyPos = gameState.getAgentPosition(enemyIndex)
                    currEnemyDist = self.getMazeDistance(currentPos, currEnemyPos)
                    if currEnemyDist < closestGhostDist:
                        closestGhostPos = currEnemyPos
                        closestGhostDist = currEnemyDist

                if closestGhostDist < 3:
                    chosenAction = None
                    minDist = 999999
                    actions = gameState.getLegalActions(self.index)
                    for action in actions:
                        nextPos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
                        dist = self.getMazeDistance(nextPos, closestGhostPos)
                        if dist < minDist:
                            minDist = dist
                            chosenAction = action


        # if on enemy's side, do MCTS
        else:
            visibleIndices = self.getVisibleEnemyIndices(gameState)
            visibleIndices.insert(0, self.index) #add teammates or no?
            # if you see a ghost, do MCTS to avoid dying i guess
            if len(visibleIndices) > 1:
                root = MCNode(gameState, None, None, self.index, visibleIndices, self) #add self to get maze distance
                chosenAction = MCTS(root)
            # otherwise, bad information, fall back on rudimentary algorithm
            else:
                chosenAction = self.backupAlgorithm(gameState)

        return chosenAction

    # the greedy algorithm of getting the closest food and returning to base after collecting pellets
    def backupAlgorithm(self, gameState):
        # base of this algorithm taken from Jeremy's initial one
        foodList = self.getFood(gameState).asList()

        # return home to get score of at least 1, put timer scamming on the table
        if self.getScore(gameState) < 1 and gameState.getAgentState( self.index ).numCarrying > 0:
            return self.returnHomeAlgo(gameState)

        # check how many total pellets left
        # if there's only 2 left or less, head home
        if len(foodList) < 3:
            return self.returnHomeAlgo(gameState)

        # check how many pellets you have #TODO: Change back to 4 or 5
        if gameState.getAgentState( self.index ).numCarrying > 4:
            return self.returnHomeAlgo(gameState)

        # otherwise head towards closest food
        agentPosn = gameState.getAgentPosition(self.index)
        closestFoodPos = None
        closestFoodDist = 1000000
        for fPosn in foodList:
            thisFoodDist = self.getMazeDistance(agentPosn, fPosn)
            if thisFoodDist < closestFoodDist:
                closestFoodDist = thisFoodDist
                closestFoodPos = fPosn

        chosenAction = None
        minDist = 1000000
        actions = gameState.getLegalActions(self.index)
        for action in actions:
            nextPos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            dist = self.getMazeDistance(nextPos, closestFoodPos)
            if dist < minDist:
                minDist = dist
                chosenAction = action

        return chosenAction

    # makes a beeline home, trying not to get killed
    def returnHomeAlgo(self, gameState):
        agentPosn = gameState.getAgentPosition(self.index)
        friendlyFoodList = self.getFoodYouAreDefending( gameState ).asList()
        closestFoodPosn = None
        closestFoodDist = 100000
        for fPosn in friendlyFoodList:
            thisFoodDist = self.getMazeDistance(agentPosn, fPosn)
            if thisFoodDist < closestFoodDist:
                closestFoodDist = thisFoodDist
                closestFoodPosn = fPosn

        chosenAction = None
        minDist = 100000
        actions = gameState.getLegalActions(self.index)

        for action in actions:
            nextPos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)
            dist = self.getMazeDistance(nextPos, closestFoodPosn)
            if dist < minDist:
                minDist = dist
                chosenAction = action

        return chosenAction

    # get the indices of enemy agents that are visible by our agents
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


'''
Class to represent the Monte Carlo Tree Node and its children
'''

# the node used for the gamestate tree of MCTS
class MCNode():

    # initalize node
    def __init__(self, gameState, parent, action, index, visibleAgentIndices, agent):
        self.avgScore = 0.0
        self.avgEval = 0.0
        self.numGames = 0
        self.gameState = gameState
        self.parent = parent
        self.children = list()  # list of MCNodes
        self.index = index  # index of this agent
        self.action = action
        self.agentForMazeDist = agent #legit it doesn't matter WHAT agent it is, but agent has helpful methods for an eval
        self.visibleAgentIndices = visibleAgentIndices

    # check if all the children of this node have been visited
    def isFullyExpanded(self):
        if len(self.children) == 0:
            return False

        if len(self.getUnusedActions()) > 0:
            return False

        for child in self.children:
            if not child.visited():
                return False

        return True

    # check if a simulation has been run on this node
    def visited(self):
        return self.numGames > 0

    # calculate the best UCT among the children of this node
    def getNodeWithBestUCT(self):
        chosenNode = None
        maxUCT = -1000000
        for child in self.children:
            if child.getUCT() > maxUCT:
                maxUCT = child.getUCT()
                chosenNode = child

        return chosenNode

    # calculate the UCT of this node
    def getUCT(self):
        exploreParam = math.sqrt(2)
        uctVal = self.avgEval + exploreParam * math.sqrt(math.log(self.parent.numGames) / self.numGames)

        return uctVal

    # check if this node has children
    def hasChildren(self):
        return len(self.children) != 0

    # get the actions from this state that have not been done
    def getUnusedActions(self):
        actions = self.gameState.getLegalActions(self.index)
        actions.remove(Directions.STOP)
        for child in self.children:
            if child.action in actions:
                actions.remove(child.action)

        return actions

    # get the next state from this node doing a random action
    def generateSuccessor(self):
        actions = self.gameState.getLegalActions(self.index)
        action = random.choice(actions)

        nextState = self.gameState.generateSuccessor(self.index, action)
        newIndex = self.getNextAgentIndex()
        successor = MCNode(nextState, self, action, newIndex, self.visibleAgentIndices, self.agentForMazeDist)

        return successor

    # get the next agent index, representing the child of this node
    def getNextAgentIndex(self):
        listIndex = self.visibleAgentIndices.index(self.index)
        listIndex = (listIndex + 1) % len(self.visibleAgentIndices)
        nextAgentIndex = self.visibleAgentIndices[listIndex]
        return nextAgentIndex

    # get the food that the current agent is allowed to eat
    def getFoodToEat(self):
        if self.gameState.isOnRedTeam(self.index):
            foodToEat = self.gameState.getBlueFood()
        else:
            foodToEat = self.gameState.getRedFood()

        return foodToEat.asList()

    # evaluation function for eating pellets and running away from ghosts
    def evalState(self):

        # GET DIST TO CLOSEST EATABLE PELLET
        # eatableFood = self.agentForMazeDist.getFood()
        agentPosn = self.gameState.getAgentPosition(self.index)
        foodPosns = self.getFoodToEat()
        closestFood = 999
        for fPosn in foodPosns:
            thisFoodDist = self.agentForMazeDist.getMazeDistance( agentPosn, fPosn )
            if thisFoodDist < closestFood:
                closestFood = thisFoodDist
        # now have closest food to use in weighting too

        # GET DIST TO CLOSEST GHOST
        enemyIndices = self.visibleAgentIndices
        closestDist = 999 #sentinel to be able to ignore
        for ind in enemyIndices:
            thisEnemyPosn = self.gameState.getAgentPosition(ind)
            thisDist = self.agentForMazeDist.getMazeDistance( agentPosn, thisEnemyPosn )
            if thisDist < closestDist:
                closestDist = thisDist
        closestDistScore = 0 #if we can't see any enemys, don't factor in running away
        if closestDist < 3: #if theres an enemy within some arbitrary distance
            closestDistScore = closestDist

        return (( 10 / (closestFood + 1) ) * 10) + closestDistScore * -5


# run Monte Carlo Tree Search
def MCTS(node):
    start = time.time()
    while 0.8 > (time.time() - start):
        leaf = search(node) # run search to the find the next candidate to expand
        simNode = expand(leaf) # expand the candidate, add to its children, return child
        resultScore = rollout(simNode) # run rollout on child of candidate
        backpropagate(simNode, resultScore)

    bestChild = best_child(node)
    return bestChild.action

# get the child of the given node with the greatest average score
def best_child(node):
    bestAvgEval = -100000
    bestChild = None
    for child in node.children:
        if child.avgEval > bestAvgEval:
            bestAvgEval = child.avgEval
            bestChild = child

    return bestChild

# choose a game state to expand and simulate on
def search(node):
    currentNode = node
    while currentNode.isFullyExpanded():
        currentNode = currentNode.getNodeWithBestUCT()

    return currentNode

# produce a child node for the given node
def expand(node):
    actions = node.getUnusedActions()
    chosenAction = random.choice(actions)
    nextState = node.gameState.generateSuccessor(node.index, chosenAction)
    newIndex = node.getNextAgentIndex()
    chosenChild = MCNode(nextState, node, chosenAction, newIndex, node.visibleAgentIndices, node.agentForMazeDist)
    node.children.append(chosenChild)

    return chosenChild


# keep choosing random actions until an end state is reached
def rollout(node):
    # potentially add depth parameter if time is an issue
    currentNode = node
    for i in range(20):
        currentNode = rollout_policy(currentNode)

    return currentNode.evalState()

# do a simulation of random moves on the given node
def rollout_policy(node):
    return node.generateSuccessor()


# update the average scores of all nodes from the given node to the root
def backpropagate(node, result):
    currentNode = node
    while currentNode is not None:
        currEval = currentNode.avgEval * currentNode.numGames
        newEval = currEval + result
        currentNode.numGames = currentNode.numGames + 1
        currentNode.avgEval = newEval / currentNode.numGames

        # set node to parent to keep looping
        currentNode = currentNode.parent
