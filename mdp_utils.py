from mdp import FeatureMDP, DrivingSimulator
import numpy as np
import math
import random

"""
Bellman Functions
"""
def value_iteration(env, epsilon=0.0001):
    """
    TODO: speed up 
  :param env: the MDP
  :param epsilon: numerical precision for values
  :return:
  """
    n = env.num_states
    V = np.zeros(n)  # could also use np.zero(n)
    Delta = np.inf #something large to make sure we enter while loop
    
    while Delta > epsilon * (1 - env.gamma) / env.gamma:
        V_old = V.copy()
        Delta = 0
        for s in range(n):
            max_action_value = -math.inf

            for a in range(env.num_actions):
                action_value = np.dot(env.transitions[s][a], V_old)
                max_action_value = max(action_value, max_action_value)
            V[s] = env.rewards[s] + env.gamma * max_action_value
            if abs(V[s] - V_old[s]) > Delta:
                Delta = abs(V[s] - V_old[s])

    return V

def policy_evaluation(policy, env, epsilon):
    """
  Evalute the policy and compute values in each state when executing the policy in the mdp
  :param policy: the policy to evaluate in the mdp
  :param env: markov decision process where we evaluate the policy
  :param epsilon: numerical precision desired
  :return: values of policy under mdp
  """
    n = env.num_states
    V = np.zeros(n)  # could also use np.zero(n)
    Delta = 10
    
    while Delta > epsilon * (1 - env.gamma) / env.gamma:
        V_old = V.copy()
        Delta = 0
        for s in range(n):
            a = policy[s]
            policy_action_value = np.dot(env.transitions[s][a], V_old)
            V[s] = env.rewards[s] + env.gamma * policy_action_value
            if abs(V[s] - V_old[s]) > Delta:
                Delta = abs(V[s] - V_old[s])

    return V

def policy_evaluation_stochastic(env, epsilon):
    # V(s) = R(s) + gamma * sum_a T(s, a, s') sum_s'[pi(s, a, s') * V(s')]
    n = env.num_states
    num_actions = env.num_actions
    V = np.zeros(n)
    delta = 10
    while delta > epsilon * (1 - env.gamma) / env.gamma:
        V_old = V.copy()
        delta = 0
        for s in range(n):
            policy_action_value = sum([np.dot(env.transitions[s][a], V_old) for a in range(num_actions)])
            V[s] = env.rewards[s] + env.gamma * 1/num_actions * policy_action_value
            delta = max(delta, abs(V[s] - V_old[s]))
    return V

def calculate_q_values(env, storage = None, V = None, epsilon = 0.0001):
    """
  gets q values for a markov decision process

  :param env: markov decision process
  :param epsilon: numerical precision
  :return: reurn the q values which are
  """

    #runs value iteration if not supplied as input
    if not V:
        V = value_iteration(env, epsilon)
        if storage:
            storage[env] = V
    n = env.num_states

    Q_values = np.zeros((n, env.num_actions))
    for s in range(n):
        for a in range(env.num_actions):
            Q_values[s][a] = env.rewards[s] + env.gamma * np.dot(env.transitions[s][a], V)
    return Q_values


"""
Policy Functions
"""
def get_optimal_policy(env, epsilon=0.0001, V=None):
    #runs value iteration if not supplied as input
    if not V:
        V = value_iteration(env, epsilon)
    n = env.num_states
    optimal_policy = []  # our game plan where we need to

    for s in range(n):
        max_action_value = -math.inf
        best_action = 0

        for a in range(env.num_actions):
            action_value = 0.0
            for s2 in range(n):  # look at all possible next states
                action_value += env.transitions[s][a][s2] * V[s2]
                # check if a is max
            if action_value > max_action_value:
                max_action_value = action_value
                best_action = a  # direction to take
        optimal_policy.append(best_action)
    return optimal_policy

def get_nonpessimal_policy(env, epsilon = 0.0001, V = None):
    if not V:
        q_values = calculate_q_values(env)
    else:
        q_values = calculate_q_values(env, V = V)
    n = env.num_states
    nonpessimal_policy = []
    for s in range(n):
        possible_actions = [i for i in range(len(q_values[s])) if q_values[s][i] != min(q_values[s])]
        if len(possible_actions) == 0:
            possible_actions.append(np.random.choice(np.array(range(env.num_actions))))
        nonpessimal_policy.append(np.random.choice(np.array(possible_actions)))
    return nonpessimal_policy

def get_worst_policy(env, V = None):
    if not V:
        q_values = calculate_q_values(env)
    else:
        q_values = calculate_q_values(env, V = V)
    n = env.num_states
    worst_policy = []
    for s in range(n):
        possible_actions = [i for i in range(len(q_values[s])) if q_values[s][i] == min(q_values[s])]
        worst_policy.append(np.random.choice(np.array(possible_actions)))
    return worst_policy

def get_random_policy(env):
    return np.random.choice(np.arange(0, env.num_actions, 1), env.num_states)


"""
Demonstration Generation Functions
"""
def generate_optimal_demo(env, start_state):
    """
    Genarates a single optimal demonstration consisting of state action pairs(s,a)
    :param env: Markov decision process passed by main see (markov_decision_process.py)
    :param beta: Beta is a rationality quantification
    :param start_state: start state of demonstration
    :return:
    """
    current_state = start_state
    max_traj_length = env.num_states  #this should be sufficiently long, maybe too long...
    optimal_trajectory = []
    q_values = calculate_q_values(env)

    while (
        current_state not in env.terminals  #stop when we reach a terminal
        and len(optimal_trajectory) < max_traj_length
    ):  # need to add a trajectory length for infinite mdps

        #generate an optimal action, break ties uniformly at random
        act = np.random.choice(arg_max_set(q_values[current_state]))
        optimal_trajectory.append((current_state, act))
        probs = env.transitions[current_state][act]
        next_state = np.random.choice(env.num_states, p=probs)
        current_state = next_state

    return optimal_trajectory

def generate_boltzman_demo(env, beta, start_state):
    """
    Genarates a single boltzman rational demonstration consisting of state action pairs(s,a)
    :param env: Markov decision process passed by main see (markov_decision_process.py)
    :param beta: Beta is a rationality quantification
    :param start_state: start state of demonstration
    :return:
    """
    current_state = start_state
    max_traj = env.num_states // 2  #this should be sufficiently long, maybe too long...
    boltzman_rational_trajectory = []
    q_values = calculate_q_values(env)

    while (
        current_state not in env.terminals  #stop when we reach a terminal
        and len(boltzman_rational_trajectory) < max_traj
    ):  # need to add a trajectory length for infinite envs

        log_numerators = beta * np.array(q_values[current_state])
        boltzman_log_probs = log_numerators - logsumexp(log_numerators)
        boltzman_probability = np.exp(boltzman_log_probs)

        bolts_act = np.random.choice([0, 1, 2, 3], p=boltzman_probability)
        boltzman_rational_trajectory.append((current_state, bolts_act))
        probs = env.transitions[current_state][bolts_act]
        next_state = np.random.choice(env.num_states, p=probs)
        current_state = next_state

    return boltzman_rational_trajectory

def demonstrate_entire_optimal_policy(env):
    opt_pi = get_optimal_policy(env)
    demo = []

    for state, action in enumerate(opt_pi):
        demo.append((state, action))

    return demo


"""
Visualization Functions
"""
def action_to_string(act, driving = False):
    if not driving:
        UP = 0
        DOWN = 1
        LEFT = 2
        RIGHT = 3
        if act == UP:
            return "^"
        elif act == DOWN:
            return "v"
        elif act == LEFT:
            return "<"
        elif act == RIGHT:
            return ">"
    else:
        STAY = 0
        LEFT = 1
        RIGHT = 2
        if act == STAY:
            return "^"
        elif act == LEFT:
            return "<"
        elif act == RIGHT:
            return ">"
    return NotImplementedError

def reverse_states(env, states):
    # TODO: make this better generalized,
    # or figure out a better lexicographical numbering for driving simulation
    # rows = env.num_rows
    # cols = env.num_cols
    rev = []
    for i in range(len(states)):
        if 0 <= i < 5:
            rev.append(states[i + 20])
        elif 5 <= i < 10:
            rev.append(states[i + 10])
        elif 10 <= i < 15:
            rev.append(states[i])
        elif 15 <= i < 20:
            rev.append(states[i - 10])
        elif 20 <= i < 25:
            rev.append(states[i - 20])
    else: # is just a list of states
        pass
    return rev

def visualize_trajectory(trajectory, env):
    """input: list of (s,a) tuples and mdp env
        ouput: prints to terminal string representation of trajectory"""
    states, actions = zip(*trajectory)
    count = 0
    for r in range(env.num_rows):
        policy_row = ""
        for c in range(env.num_cols):
            if count in states:
                #get index
                indx = states.index(count)
                if count in env.terminals:
                    policy_row += ".\t"    
                else:    
                    # policy_row += action_to_string(actions[indx], type(env) is DrivingSimulator) + "\t"
                    policy_row += action_to_string(actions[indx]) + "\t"
            else:
                policy_row += " \t"
            count += 1
        print(policy_row)

def visualize_policy(policy, env):
    """
  prints the policy of the MDP using text arrows and uses a '.' for terminals
  """
    count = 0
    for r in range(env.num_rows):
        policy_row = ""
        for c in range(env.num_cols):
            if count in env.terminals:
                policy_row += ".\t"
            else:
                policy_row += action_to_string(policy[count], driving = isinstance(env, DrivingSimulator)) + "\t"
            count += 1
        print(policy_row)

def visualize_env(env):
    if type(env) is DrivingSimulator:
        reversed_motorists = env.motorists[::-1]
        border = "-" * 8 * env.num_cols + "-"
        print(border)
        count = 0
        for r in range(env.num_rows):
            env_row = "|"
            for c in range(env.num_cols):
                if count in reversed_motorists:
                    env_row += "   C   "
                elif count % env.num_cols == 0 or count % env.num_cols == env.num_cols - 1:
                    env_row += "   X   "
                else:
                    env_row += "       "
                env_row += "|"
                count += 1
            print(env_row)
            print(border)

def visualize_binary_features(env):
    #takes as input mdp_env and prints out a human readable grid of features numbered 0 to K-1, where K is number of reward
    #features. Note this method assumes binary (one-hot) features
    assert(type(env) is FeatureMDP)
    feature_values = [list(f).index(1) for f in env.state_features]
    print_array_as_grid_raw(feature_values, env)

def print_array_as_grid(array_values, env):
    """
  Prints array as a grid
  :param array_values:
  :param env:
  :return:
  """
    count = 0
    for r in range(env.num_rows):
        print_row = ""
        for c in range(env.num_cols):
            print_row += "{:.2f}\t".format(array_values[count])
            count += 1
        print(print_row)

def print_array_as_grid_raw(array_values, env):
    """
  Prints array as a grid
  :param array_values:
  :param env:
  :return:
  """
    count = 0
    for r in range(env.num_rows):
        print_row = ""
        for c in range(env.num_cols):
            print_row += "{}\t".format(array_values[count])
            count += 1
        print(print_row)


"""
Math Helper Functions
"""
def logsumexp(x):
    max_x = np.max(x)
    sum_exp = 0.0
    for xi in x:
        sum_exp += np.exp(xi - max_x)
    return max(x) + np.log(sum_exp)

def arg_max_set(values, eps=0.0001):
    # return a set of the indices that correspond to the maximum element(s) in the set of values
    # input is a list or 1-d array and eps tolerance for determining equality
    max_val = max(values)
    arg_maxes = []  # list for storing the indices to the max value(s)
    for i, v in enumerate(values):
        if abs(max_val - v) < eps:
            arg_maxes.append(i)
    return arg_maxes

def sample_l2_ball(k):
    #sample a vector of dimension k with l2 norm of 1
    sample = np.random.randn(k)
    return sample / np.linalg.norm(sample)

def two_norm_diff(x, y, length):
    sum_squares = 0
    for i in range(length):
        diff = x[i] - y[i]
        sum_squares += diff**2
    return sum_squares


"""
Stopping Condition Functions
"""
def calculate_expected_value_difference(eval_policy, env, storage, epsilon = 0.0001, rn = False):
    '''calculates the difference in expected returns between an optimal policy for an mdp and the eval_policy'''
    if env in storage:
        V_opt = storage[env]
    else:
        V_opt = value_iteration(env, epsilon)
    V_eval = policy_evaluation(eval_policy, env, epsilon)
    if rn:
        V_rand = policy_evaluation_stochastic(env, epsilon)
        if (np.mean(V_opt) - np.mean(V_eval)) == 0:
            return 0.0
        return (np.mean(V_opt) - np.mean(V_eval)) / (np.mean(V_opt) - np.mean(V_rand))
    return np.mean(V_opt) - np.mean(V_eval)

def find_nonterminal_uncertainties(metrics, k, env, queried_states, query_type, repeats_allowed, avoid_states):
    if query_type == "evd":
        metrics = np.sort(metrics, axis = 0)
        metric = metrics[k]
        state_losses = sorted(list(enumerate(metric)), key = lambda s : s[1]) # (state, evd)
        terminal_losses = set([(term, metric[term]) for term in env.terminals])
        losses = np.copy(metric)
        uncertain = state_losses[-1]
        if repeats_allowed:
            while uncertain[0] in env.terminals or uncertain[0] in avoid_states:
                state_losses = state_losses[:-1]
                losses = np.delete(losses, np.argwhere(losses == uncertain[1]))
                if len(set(losses)) == 1:
                    uncertain = random.choice(list(set(state_losses).difference(terminal_losses)))
                    break
                else:
                    try:
                        uncertain = state_losses[-1]
                    except:
                        break
        else:
            while uncertain[0] in env.terminals or uncertain[0] in queried_states or uncertain[0] in avoid_states:
                state_losses = state_losses[:-1]
                losses = np.delete(losses, np.argwhere(losses == uncertain[1]))
                if len(set(losses)) == 1:
                    uncertain = random.choice(list(set(state_losses).difference(terminal_losses)))
                    break
                else:
                    try:
                        uncertain = state_losses[-1]
                    except:
                        break
        uncertain_state = uncertain[0]
        avar_bound = metric[uncertain_state]
    elif query_type == "improvement": ### not in use for now!!!
        metric = np.var(metrics, axis = 0)
        uncertain_state = np.argmax(metric)
        avar_bound = metric[uncertain_state]
    return avar_bound, uncertain_state

def calculate_state_and_policy_metrics(eval_policy, env, storage, query_type, bound_type, base_policy = None, epsilon = 0.0001, rn = False):
    """
    `query_type` dictates the state metric: "evd" or % "improvement" (variance)
    `bound_type` dictates the policy metric: "nevd" or "baseline"
    `rn` is just for nEVD random normalization
    """
    V_eval = np.array(policy_evaluation(eval_policy, env, epsilon))
    if query_type == "evd" and bound_type == "nevd":
        if env in storage:
            V_opt = np.array(storage[env])
        else:
            V_opt = np.array(value_iteration(env, epsilon))
        state_metric = np.nan_to_num(np.array([V_opt - V_eval]))
        if rn:
            V_rand = np.array(policy_evaluation_stochastic(env, epsilon))
            # print("V_opt = {}, V_eval = {}, V_rand = {}; {} / {} = {}".format(V_opt, V_eval, V_rand, V_opt - V_eval, V_opt - V_rand, (V_opt - V_eval) / (V_opt - V_rand)))
            policy_metric = np.nan_to_num((np.mean(V_opt) - np.mean(V_eval)) / (np.mean(V_opt) - np.mean(V_rand)))
        else:
            policy_metric = np.mean(V_opt) - np.mean(V_eval)
    elif query_type == "evd" and bound_type == "baseline":
        if env in storage:
            V_opt = np.array(storage[env])
        else:
            V_opt = np.array(value_iteration(env, epsilon))
        state_metric = np.nan_to_num(np.array([V_opt - V_eval]))
        V_base = np.array(policy_evaluation(base_policy, env, epsilon))
        policy_metric = np.nan_to_num((np.mean(V_eval) - np.mean(V_base)) / np.abs(np.mean(V_base)))
    elif query_type == "improvement" and bound_type == "nevd":
        pass
    elif query_type == "improvement" and bound_type == "baseline":
        V_base = np.array(policy_evaluation(base_policy, env, epsilon))
        state_metric = np.nan_to_num(np.array([(V_eval - V_base) / np.abs(V_base)]))
        policy_metric = (np.mean(V_eval) - np.mean(V_base)) / np.abs(np.mean(V_base))
    return state_metric, policy_metric

def calculate_state_percent_improvement(env, base_policy, eval_policy, epsilon = 0.0001):
    V_base = policy_evaluation(base_policy, env, epsilon)
    V_eval = policy_evaluation(eval_policy, env, epsilon)
    # print("MEAN METRICS")
    # print(np.mean(V_base), np.mean(V_eval), (np.mean(V_eval) - np.mean(V_base)) / np.abs(np.mean(V_base)))
    return np.nan_to_num(np.array([(V_eval - V_base) / np.abs(V_base)]))

def calculate_policy_accuracy(opt_pi, eval_pi):
    assert len(opt_pi) == len(eval_pi)
    matches = 0
    for i in range(len(opt_pi)):
        matches += opt_pi[i] == eval_pi[i]
    return matches / len(opt_pi)

def calculate_percentage_optimal_actions(pi, env, epsilon=0.0001):
    # calculate how many actions under pi are optimal under the env
    accuracy = 0.0
    # first calculate the optimal q-values under env
    q_values = calculate_q_values(env, epsilon=epsilon)
    # then check if the actions under pi are maximizing the q-values
    for state, action in enumerate(pi):
        if action in arg_max_set(q_values[state], epsilon):
            accuracy += 1  # policy action is an optimal action under env

    return accuracy / env.num_states

def calculate_number_of_optimal_actions(env, pi, demos, exact, epsilon=0.0001):
    optimal = 0
    if exact:
        for s, a in demos:
            if pi[s] == a:
                optimal += 1
    else:
        states = [s for s, _ in demos]
        q_values = calculate_q_values(env, epsilon=epsilon)
        for state in states:
            if pi[state] in arg_max_set(q_values[state], epsilon):
                optimal += 1
    return optimal

def calculate_percent_improvement(env, base_policy, eval_policy, epsilon = 0.0001):
    V_base = policy_evaluation(base_policy, env, epsilon)
    V_eval = policy_evaluation(eval_policy, env, epsilon)
    return np.mean(V_base), np.mean(V_eval), (np.mean(V_eval) - np.mean(V_base)) / np.abs(np.mean(V_base))


"""
Feature Count Bound and Other Bounds Functions
"""
def calculate_empirical_expected_fc(env, trajectories):
    """
    env: the FeatureMDP
    trajectories: list of lists of demonstrations
    """
    num_features = env.num_features
    gamma = env.gamma
    state_features = env.state_features
    avg_feature_counts = np.zeros(num_features)
    for traj in trajectories:
        for d in range(len(traj)):
            demo = traj[d]
            for f in range(num_features):
                avg_feature_counts[f] += gamma**d * state_features[demo[0]][f]
    avg_feature_counts /= len(trajectories)
    return avg_feature_counts

def calculate_state_expected_fc(pi, env, epsilon = 0.0001, random = False):
    num_states = env.num_states
    num_features = env.num_features
    num_actions = env.num_actions
    state_features = env.state_features
    gamma = env.gamma
    transitions = env.transitions
    feature_counts = np.zeros((num_states, num_features))
    delta = 1

    if not random:
        while delta > epsilon:
            delta = 0
            for s1 in range(num_states):
                temp = np.zeros(num_features)
                for f in range(num_features):
                    temp[f] += state_features[s1][f]
                action = pi[s1]
                transition_features = np.zeros(num_features)
                for s2 in range(num_states):
                    if transitions[s1][action][s2] > 0:
                        for f in range(num_features):
                            transition_features[f] += transitions[s1][action][s2] * feature_counts[s2][f]
                for f in range(num_features):
                    temp[f] += gamma * transition_features[f]
                    delta = max(delta, abs(temp[f] - feature_counts[s1][f]))
                    feature_counts[s1][f] = temp[f]
    else:
        while delta > epsilon:
            delta = 0
            for s1 in range(num_states):
                temp = np.zeros(num_features)
                for f in range(num_features):
                    temp[f] += state_features[s1][f]
                transition_features = np.zeros(num_features)                
                for s2 in range(num_states):
                    for action in range(num_actions):
                        if transitions[s1][action][s2] > 0:
                            for f in range(num_features):
                                transition_features[f] += (1/num_actions) * transitions[s1][action][s2] * feature_counts[s2][f]
                for f in range(num_features):
                    temp[f] += gamma * transition_features[f]
                    delta = max(delta, abs(temp[f] - feature_counts[s1][f]))
                    feature_counts[s1][f] = temp[f]
    
    return feature_counts

def calculate_expected_fc(pi, env, epsilon = 0.0001, random = False):
    """
    pi: eval policy
    env: the featureMDP
    """
    if not random:
        state_feature_counts = calculate_state_expected_fc(pi, env, epsilon = epsilon)
    else:
        state_feature_counts = calculate_state_expected_fc(pi, env, epsilon = epsilon, random = True)
    num_states = env.num_states
    num_features = env.num_features

    expected_fc = np.zeros(num_features)
    for s in range(num_states):
        for f in range(num_features):
            expected_fc[f] += state_feature_counts[s][f]
    expected_fc /= num_states # assuming any state can be an initial state
    return expected_fc

def calculate_wfcb(pi, env, trajectories, epsilon = 0.0001):
    """
    pi: eval policy
    env: the FeatureMDP
    trajectories: list of lists of demonstrations
    """
    mu_hat_star = calculate_empirical_expected_fc(env, trajectories)
    mu_pi_eval = calculate_expected_fc(pi, env, epsilon = epsilon)
    mu_pi_rand = calculate_expected_fc(pi, env, epsilon = epsilon, random = True)
    max_abs_diff = np.max(np.abs(mu_hat_star - mu_pi_eval)) / np.max(np.abs(mu_hat_star - mu_pi_rand))
    return max_abs_diff

def syed_schapire_bound(num_demos, gamma, num_features, delta):
    return 3/(1 - gamma) * np.sqrt(2/num_demos * np.log(2*num_features / delta))

def abbeel_bound(num_demos, gamma, num_features, delta):
    return 1/(1 - gamma) * np.sqrt(2*num_features / num_demos * np.log(2*num_features / delta))


if __name__ == "__main__":
    fw = np.array([0, 1, -100, -100000])
    blank = np.array([1, 0, 0, 0])
    one = np.array([0, 1, 0, 0])
    hunnit = np.array([0, 0, 1, 0])
    x = np.array([0, 0, 0, 1])
    sf = np.array([
        blank, blank, blank, one,
        blank, x, blank, hunnit,
        blank, blank, blank, blank
    ])
    test = FeatureMDP(3, 4, 4, [3, 7], fw, sf, 0.7, noise = 0.0, driving = False)
    # print(value_iteration(test))
    # state_evds = np.array([[0 for _ in range(12)]])
    # for i in range(3):
    #     test.set_rewards([i, i, i, i])
    #     state_evds = np.append(state_evds, calculate_state_expected_value_difference([0 for _ in range(12)], test, [], epsilon = 0.0001, rn = False), axis = 0)
    # k = 2
    # print(state_evds)
    # state_evds = np.delete(state_evds, 0, axis = 0)
    # state_evds = np.sort(state_evds, axis = 0)
    # avar_bound, uncertain_state = np.max(state_evds[k]), np.argmax(state_evds[k])
    # print(state_evds)
    # print(avar_bound)
    # print(uncertain_state)
