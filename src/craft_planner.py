import json
from collections import namedtuple, defaultdict, OrderedDict
from timeit import default_timer as time
from math import inf, ceil
from heapq import heappush,heappop

Recipe = namedtuple('Recipe', ['name', 'check', 'effect', 'cost'])


class State(OrderedDict):
    """ This class is a thin wrapper around an OrderedDict, which is simply a dictionary which keeps the order in
        which elements are added (for consistent key-value pair comparisons). Here, we have provided functionality
        for hashing, should you need to use a state as a key in another dictionary, e.g. distance[state] = 5. By
        default, dictionaries are not hashable. Additionally, when the state is converted to a string, it removes
        all items with quantity 0.

        Use of this state representation is optional, should you prefer another.
    """

    def __key(self):
        return tuple(self.items())

    def __hash__(self):
        return hash(self.__key())

    def __lt__(self, other):
        return self.__key() < other.__key()

    def __gt__(self, other):
        return self.__key() > other.__key()


    def __ne__(self, other):
        return not (self == other)

    def copy(self):
        new_state = State()
        new_state.update(self)
        return new_state

    def __str__(self):
        return str(dict(item for item in self.items() if item[1] > 0))


def make_checker(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].

        if 'Consumes' in rule.keys():
            for c_item, c_value in rule['Consumes'].items():
                if c_item not in state.keys():
                    return False
                if state[c_item] < c_value:
                    return False

        if 'Requires' in rule.keys():
            for r_item, r_value in rule['Requires'].items():
                if r_item not in state.keys():
                    return False
                if state[r_item] ==0:
                    return False
        return True

    return check

def make_checker_for_heur(rule):
    # Implement a function that returns a function to determine whether a state meets a
    # rule's requirements. This code runs once, when the rules are constructed before
    # the search is attempted.

    def check(state):
        # This code is called by graph(state) and runs millions of times.
        # Tip: Do something with rule['Consumes'] and rule['Requires'].
        if 'Produces' in rule.keys():
            for p_item, p_value in rule['Produces'].items():
                if p_item not in state.keys():
                    return False
                if state[p_item] <= 0:
                    return False

        return True

    return check

def make_rev_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].

        if 'Consumes' in rule.keys():
            for c_item, c_value in rule['Consumes'].items():
                if c_item in state.keys():
                    state[c_item] += c_value
                else:
                    state[c_item] = c_value

        if 'Produces' in rule.keys():
            for p_item, p_value in rule['Produces'].items():
                state[p_item] -= p_value
        return state

    return effect

def make_effector(rule):
    # Implement a function that returns a function which transitions from state to
    # new_state given the rule. This code runs once, when the rules are constructed
    # before the search is attempted.

    def effect(state):
        # This code is called by graph(state) and runs millions of times
        # Tip: Do something with rule['Produces'] and rule['Consumes'].
        next_state = state.copy()

        if 'Consumes' in rule.keys():
            for c_item, c_value in rule['Consumes'].items():
                if c_item in next_state.keys():
                    next_state[c_item] -= c_value


        if 'Produces' in rule.keys():
            for p_item, p_value in rule['Produces'].items():
                if p_item in next_state.keys():
                    next_state[p_item] += p_value
                else:
                    next_state[p_item] = p_value

        return next_state

    return effect


def make_goal_checker(goal):
    # Implement a function that returns a function which checks if the state has
    # met the goal criteria. This code runs once, before the search is attempted.

    def is_goal(state):
        # This code is used in the search process and may be called millions of times.
        for g_item, g_value in goal.items():
            if g_item in state.keys():
                if state[g_item] < g_value:
                     return False
            else:
                return False
        return True

    return is_goal


def graph(state):
    # Iterates through all recipes/rules, checking which are valid in the given state.
    # If a rule is valid, it returns the rule's name, the resulting state after application
    # to the given state, and the cost for the rule.
    for r in all_recipes:
        if r.check(state):
            yield (r.name, r.effect(state), r.cost)

def get_missing(currentState, targetState):
    for t_item, t_value in targetState.items():
        #diffState[t_item]= -t_value
        if t_item in currentState:
            targetState[t_item] -= currentState[t_item]
    return targetState

def heur(state):
    for s_item, s_value in state.items():
        if (s_item=="bench" or s_item== "furnace" or s_item== "iron_axe" or s_item == "iron_pickaxe" or \
                        s_item=="stone_axe" or s_item=="stone_pickaxe" or s_item=="wooden_axe"  \
                        or s_item=="wooden_pickaxe") and s_value>=2:
            return inf
    return 0
def heuristic(state):
    # Implement your heuristic here!

    if is_goal(state):
        return 0
    for s_item, s_value in state.items():
        if (s_item=="bench" or s_item== "furnace" or s_item== "iron_axe" or s_item == "iron_pickaxe" or \
                        s_item=="stone_axe" or s_item=="stone_pickaxe" or s_item=="wooden_axe"  \
                        or s_item=="wooden_pickaxe") and s_value>=2:
            return inf
    goal_state = State({key: 0 for key in Crafting['Items']})
    goal_state.update(Crafting['Goal'])
    diffState=get_missing(state,goal_state)
    heur=0
    while True:
        break_check=True
        for d_item, d_value in diffState.items():
            if d_value>0:
                break_check=False
                rule, p_number, rule_time = fastest_rule(d_item)
                heur_efector = make_rev_effector(rule)
                for i in range(ceil(1.0*d_value/p_number)):
                    heur_efector(diffState)
                    heur+=rule_time
        if break_check:
            break
    #print('heur for this node is :',heur)

    return heur

def fastest_rule(item):
    ret_rule=None
    rule_time=inf
    rule_value=0
    for name, rule in Crafting['Recipes'].items():
        for p_item, p_value in rule['Produces'].items():
            if p_item==item:
                if rule['Time']<rule_time:
                    rule_time=rule['Time']
                    ret_rule=rule
                    rule_value=p_value
    return (ret_rule,rule_value,rule_time)
compute_time=0
game_time=0
def search(graph, state, is_goal, limit, heuristic):

    start_time = time()

    # Implement your search here! Use your heuristic here!
    # When you find a path to the goal return a list of tuples [(state, action)]
    # representing the path. Each element (tuple) of the list represents a state
    # in the path and the action that took you to this state

    #while time() - start_time < limit:
    #    pass

    Q=[]
    heappush(Q,(0,state))
    #for i in range(10):
    came_from_and_action = {}
    costs_so_far = {state:0}
    came_from_and_action[state]=(0,0)
    #for i in range(3):
    while Q and time() - start_time < limit:
        score , current_state = heappop(Q)

        #print('min game time:',score )
        if is_goal(current_state):
            global game_time
            game_time = costs_so_far[current_state]
            global compute_time
            compute_time= time()-start_time
            return_list=[]
            while(came_from_and_action[current_state] != (0,0)):
                came_from, action = came_from_and_action[current_state]
                #print(current_state, ' ', action)
                return_list.append ((current_state, action))
                current_state=came_from

            return reversed(return_list)
        '''
        for x,y in costs_so_far.items():
            print('x: ',x)
            print('y: ', y)
        '''
        for action, next_state, t in graph(current_state):
            new_cost=costs_so_far[current_state]+t

            if next_state not in costs_so_far or new_cost<costs_so_far[next_state]:
                #h=heuristic(next_state)

                heappush(Q, (new_cost+ heuristic(next_state), next_state))
                came_from_and_action[next_state]=(current_state,action)
                costs_so_far[next_state]=new_cost

    # Failed to find a path

    print(time() - start_time, 'seconds.')
    print("Failed to find a path from", state, 'within time limit.')
    return None

if __name__ == '__main__':
    with open('crafting.json') as f:
        Crafting = json.load(f)

    # List of items that can be in your inventory:
    print('All items:', Crafting['Items'])

    # List of items in your initial inventory with amounts:
    #print('Recipes:', Crafting['Recipes'][0])

    # List of items needed to be in your inventory at the end of the plan:
    print('Goal:',Crafting['Goal'])
    print('Initial: ',Crafting['Initial'])

    # Dict of crafting recipes (each is a dict):
    #print('Example recipe:','craft stone_pickaxe at bench ->',Crafting['Recipes']['craft stone_pickaxe at bench'])

    # Build rules
    all_recipes = []
    all_heur_recipes = []


    for name, rule in Crafting['Recipes'].items():
        checker = make_checker(rule)
        effector = make_effector(rule)
        recipe = Recipe(name, checker, effector, rule['Time'])
        all_recipes.append(recipe)
        heur_checker = make_checker_for_heur(rule)



    # Create a function which checks for the goal
    is_goal = make_goal_checker(Crafting['Goal'])


    # Initialize first state from initial inventory
    state = State({key: 0 for key in Crafting['Items']})
    state.update(Crafting['Initial'])

    # Search for a solution

    resulting_plan = search(graph, state, is_goal, 30, heuristic)

    if resulting_plan:
        # Print resulting plan
        leng=0
        for state, action in resulting_plan:
            print('\t',state)
            print(action)
            leng+=1
        print('game time: ' + str(game_time))
        print('game length: ',leng)
        print('compute time: ', str(compute_time))

