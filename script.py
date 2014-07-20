#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
import re, gv, sys
import ply.lex as lex
import ply.yacc as yacc
from pypepa import PEPAModel

# Dictionary containing all named workflows so far created (unnamed ones will later be given a name and added to it)
# Each value is a Workflow() object and each key is the respective workflow name
workflows = {}

# List containing all unnamed Workflow() objects so far created
unnamed_workflows = []

def main():
    # Search for 'workflows' in global namespace
    global workflows

    # Regular expression for extracting each workflow from data
    p = re.compile(r"digraph\s*[^{}]*\s*{[^{}]*}")

    """
    Read input files
    """

    # List containing all workflows read so far
    # Each value is the string of a single input workflow
    data = []

    # Only accept as input file names arguments after the current script name
    args = sys.argv[sys.argv.index(__file__) + 1:]

    # Read the data from each input file
    for arg in args:
        with open(arg, 'r') as f:
            datum = f.read()
            data += p.findall(datum)

    # Initialize a Workflow() object from each 'data' value
    map(init_graph, data)

    """
    Name unnamed Workflow() objects
    """

    # Argument for formatted output, so all workflow names have the same number of digits, using '0' as a filler
    # Useful for keeping output files sorted
    n = len(unnamed_workflows)
    decimals = len(str(n))
    number = "{{0:0{0}d}}".format(str(decimals))

    for i in range(n):
        # 'i' is an index of list 'unnamed_workflows'.

        # Create current Workflow() object name
        name = 'workflow' + number.format(i + 1)

        # Add it to the object
        unnamed_workflows[i].name = name

        # And append the object to dictionary 'workflows'
        workflows[name] = unnamed_workflows[i]

    # Now that all read workflows are in dictionary 'workflows', we can iterate through them and perform the next steps
    for wkf in workflows.values():
        try:
            process_wkf(wkf)
        except:
            print('There was an error while processing {0}. :('.format(wkf.name))
            print('Traceback was logged to "{0}_traceback".\n'.format(wkf.name))

            with open('{0}_traceback'.format(wkf.name), 'w') as f:
                f.write(traceback.format_exc())
        else:
            print('{0} was sucessfully processed! :D'.format(wkf.name))
            print('Output files were created.\n')

class Node(object):
    def __init__(self):
        self.name = None
        self.type = None
        self.rate = None
        self.predecessors = []
        self.sucessors = []

    def __str__(self):
        return self.name

    def __repr__(self):
        string  = ['Node:']

        string += ['\tName: {0}'.format(self.name)]
        string += ['\tType: {0}'.format(self.type)]
        string += ['\tRate: {0}'.format(self.rate)]
        string += ['\tPredecessors: {0}'.format(str(map(str,self.predecessors)))]
        string += ['\tSucessors:    {0}'.format(str(map(str,self.sucessors)))]

        return '\n'.join(string)

class Edge(object):
    def __init__(self):
        self.tail = None
        self.head = None
        self.prob = None

    def __str__(self):
        return "{0} -> {1}".format(self.tail.name, self.head.name)

    def __repr__(self):
        string  = ['Edge:']

        string += ['\tTail: {0}'.format(self.tail.name)]
        string += ['\tHead: {0}'.format(self.head.name)]
        string += ['\tProb: {0}'.format(str(self.prob))]

        return '\n'.join(string)

class Workflow(object):
    def __init__(self):
        self.name  = None
        self.nodes = {}
        self.edges = {}
        self.pepa  = {'act_rates'   : [],
                      'probs'       : [],
                      'xor_rates'   : [],
                      'branches'    : [],
                      'master'      : '',
                      'sync'        : [],
                      'op_rates'    : ['r_AND = 100.0;',
                                       'r_XOR = 100.0;',
                                       'r_OR  = 100.0;']}

    def __str__(self):
        string = ["Workflow:"]

        string += ['\t' + "Name: " + self.name]
        string += ['\t' + "Nodes: " + str(self.nodes.keys())]
        string += ['\t' + "Edges: " + str(map(str, self.edges.values()))]

        return '\n'.join(string)

    def add_node(self, name, type = 'ACT', rate = 1):
        n = Node()
        n.name = name
        n.type = type
        n.rate = rate

        self.nodes[name] = n

    def add_edge(self, tail, head, prob = 1):
        e = Edge()
        e.tail = self.nodes[tail]
        e.head = self.nodes[head]
        e.prob = prob

        self.edges[(tail, head)] = e

        e.head.predecessors += [e.tail]
        e.tail.sucessors += [e.head]

    def has_node(self, name):
        return name in self.nodes

    def has_edge(self, tail, head):
        return (tail, head) in self.edges

    def root_node(self):
        for node in self.nodes.values():
            if node.predecessors == []:
                return node

def init_graph(data):
    # List of token names (always required!)
    reserved = {
        'digraph' : 'DIGRAPH',
        'or' : 'OR', 'OR' : 'OR', 'Or' : 'OR', 'oR' : 'OR',
        'and' : 'AND', 'And' : 'AND', 'aNd' : 'AND', 'anD' : 'AND', 'aND' : 'AND', 'AnD' : 'AND', 'ANd' : 'AND', 'AND' : 'AND',
        'xor' : 'XOR', 'Xor' : 'XOR', 'xOr' : 'XOR', 'xoR' : 'XOR', 'xOR' : 'XOR', 'XoR' : 'XOR', 'XOr' : 'XOR', 'XOR' : 'XOR',
    }

    tokens = [
        'OPEN_BRACE',
        'CLOSE_BRACE',
        'OPEN_BRACKET',
        'CLOSE_BRACKET',
        'EDGEOP',
        'ID',
        'NUMBER',
        'COMMA',
        'SEMICOLON',
        'OR',
        'AND',
        'XOR',
        'DIGRAPH'
    ]

    # Regular expression rules for simple tokens
    t_OPEN_BRACE = r'\{'
    t_CLOSE_BRACE = r'\}'
    t_OPEN_BRACKET = r'\['
    t_CLOSE_BRACKET = r'\]'
    t_EDGEOP = r'->'
    t_COMMA = r','
    t_SEMICOLON = r';'

    # A regular expression rule with some action code
    def t_ID(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'ID')
        return t

    def t_NUMBER(t):
        r'\d+\.\d+|\d+'
        t.value = float(t.value)
        return t

    # Define a rule so we can track line numbers
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'

    # Error handling rule
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer
    lexer = lex.lex()

    # Give the lexer some input
    lexer.input(data)

    # Create the digraph
    wkf = Workflow()

    # Parser expressions

    # Define digraph name and attribute it to global variable 'wkfname'
    def p_digraph_id(t):
        'digraph : DIGRAPH ID OPEN_BRACE stmt CLOSE_BRACE'
        wkf.name = t[2]

    def p_digraph_no_id(t):
        'digraph : DIGRAPH OPEN_BRACE stmt CLOSE_BRACE'
        pass

    def p_stmtlist(t):
        'stmt : stmt stmt'

    # Create the edges
    def p_stmt(t):
        'stmt : node edge SEMICOLON'

        tail = t[1]
        edge_list = t[2]

        for head, prob in edge_list:
            wkf.add_edge(tail, head, prob)

    # Create each node or update its attributes if it already exists
    def p_node_atrr_op_or(t):
        'node : ID OPEN_BRACKET OR CLOSE_BRACKET EDGEOP'

        name = t[1]
        type = 'OR'
        rate = None

        t[0] = name

        if wkf.has_node(name):
            wkf.nodes[name].type = type
            wkf.nodes[name].rate = rate
        else:
            wkf.add_node(name, type, rate)

    def p_node_atrr_op_xor(t):
        'node : ID OPEN_BRACKET XOR CLOSE_BRACKET EDGEOP'

        name = t[1]
        type = 'XOR'
        rate = None

        t[0] = name

        if wkf.has_node(name):
            wkf.nodes[name].type = type
            wkf.nodes[name].rate = rate
        else:
            wkf.add_node(name, type, rate)

    def p_node_atrr_op_and(t):
        'node : ID OPEN_BRACKET AND CLOSE_BRACKET EDGEOP'

        name = t[1]
        type = 'AND'
        rate = None

        t[0] = name

        if wkf.has_node(name):
            wkf.nodes[name].type = type
            wkf.nodes[name].rate = rate
        else:
            wkf.add_node(name, type, rate)

    def p_node_attr_num(t):
        'node : ID OPEN_BRACKET NUMBER CLOSE_BRACKET EDGEOP'

        name = t[1]
        type = 'ACT'
        rate = t[3]

        t[0] = name

        if wkf.has_node(name):
            wkf.nodes[name].type = type
            wkf.nodes[name].rate = rate
        else:
            wkf.add_node(name, type, rate)

    def p_node_attr_none(t):
        'node : ID EDGEOP'

        name = t[1]
        type = 'ACT'
        rate = 1.0

        t[0] = name

        if wkf.has_node(name):
            wkf.nodes[name].type = type
            wkf.nodes[name].rate = rate
        else:
            wkf.add_node(name, type, rate)

    def p_edge_list(t):
        'edge : edge COMMA edge'
        t[0] = t[1] + t[3]

    # Create nodes not yet created so later the edges can be created
    # Attributes will be added later
    def p_edge_prob(t):
        'edge : OPEN_BRACKET NUMBER CLOSE_BRACKET ID'

        head = t[4]
        type = 'ACT'
        rate = 1.0

        prob = t[2]

        t[0] = [(head, prob)]

        if not wkf.has_node(head):
            wkf.add_node(head, type, rate)

    def p_edge_no_prob(t):
        'edge : ID'

        head = t[1]
        type = 'ACT'
        rate = 1.0

        prob = 1.0

        t[0] = [(head, prob)]

        if not wkf.has_node(head):
            wkf.add_node(head, type, rate)

    # Error handling
    def p_error(t):
        print("Syntax error at '%s'" % t.value)

    # Build the parser
    yacc.yacc()
    yacc.parse(data)

    # Add Workflow() object to global sets depending on whether it's named
    if wkf.name == None:
        global unnamed_workflows
        unnamed_workflows += [wkf]
    else:
        global workflows
        workflows[wkf.name] = wkf

def process_wkf(wkf):
    # 'wkf' is a Workflow() object in dictionary 'workflows'

    # Put the first node of 'wkf' in 'node_0'
    node_0 = wkf.root_node()

    # Traverse 'wkf', generating it's PEPA description meanwhile
    traverse(wkf, node_0)

    # Generate 'wkf's DOT description and it's visualization, writing both to output files
    dot_pdf(wkf)

    # Join all strings inside dictionary 'wkf.pepa'
    pepa  = []
    pepa += ['\n'.join(wkf.pepa['act_rates'])]
    pepa += ['\n'.join(wkf.pepa['op_rates'])]
    pepa += ['\n'.join(wkf.pepa['probs'])]
    pepa += ['\n'.join(wkf.pepa['xor_rates'])]
    pepa += [wkf.pepa['master']]
    pepa += ['\n'.join(wkf.pepa['branches'])]
    pepa += [''.join(wkf.pepa['sync'])]
    pepa  = '\n\n'.join(pepa)

    # Write PEPA description to an output file
    with open(wkf.name + '.pepa', 'w') as f:
        f.write(pepa)

    # Solve the PEPA model
    solution = solve_pepa(pepa)

    with open(wkf.name + '_solution', 'w') as f:
        f.write(solution)

def write(wkf):
    dot = []

    dot += "digraph {0} {{\n".format(wkf.name)

    for node in wkf.nodes.values():
        dot += "\t{0} ".format(node.name)
        if node.type == 'ACT':
            dot += "[shape=box,\t\tlabel={0}];\n".format(node.name)
        else:
            if node.type == 'AND':
                color = 'blue'
            elif node.type == 'OR':
                color = 'red'
            elif node.type == 'XOR':
                color = 'green'

            dot += "[shape=diamond,\tlabel={0},\tcolor={1}];\n".format(node.name, color)

    for edge in wkf.edges.values():
        dot += "\t{0} -> {1}".format(edge.tail, edge.head)
        if edge.prob != 1.0:
            dot += ' [label="{0}"]'.format(edge.prob)

        dot += ';\n'

    dot += "}"
    return ''.join(dot)

def dot_pdf(wkf):
    # Write to DOT language and create a pdf file of the digraph with its name
    dot = write(wkf)

    with open(wkf.name + '.dot', 'w') as f:
        f.write(dot)

    gvv = gv.readstring(dot)
    gv.layout(gvv,'dot')
    gv.render(gvv,'pdf', wkf.name + '.pdf')

def traverse_AND(wkf, AND_A):
    sucs = AND_A.sucessors
    S = []

    for suc in sucs:
        S += ['P_{0}_{1}'.format(AND_A.name, suc.name)]

        P  = []
        P += ['P_{0}_{1}'.format(AND_A.name, suc.name)]
        P += ['=']
        P += ['({0}, r_AND)'.format(AND_A.name)]
        P += ['.']

        node = suc
        while len(node.predecessors) == 1:
            if node.type == 'ACT':
                P += ['({0}, r_{0})'.format(node.name)]
                P += ['.']

                wkf.pepa['act_rates'] += ['r_{0} = {1};'.format(node.name, node.rate)]
                node = node.sucessors[0]

            elif node.type == 'AND':
                and_a = node
                P += ['({0}, r_AND)'.format(and_a.name)]
                P += ['.']

                and_b, sync = traverse_AND(wkf, and_a)
                S += ['(' + sync + ')']
                P += ['({0}, r_AND)'.format(and_b)]
                P += ['.']

                node = and_b.sucessors[0]

            elif node.type == 'XOR':
                xor_a = node

                P += ['P_{0}'.format(xor_a.name)]

                branch = '{0};'.format(' '.join(P))
                wkf.pepa['branches'] += [branch]

                xor_b, sync = traverse_XOR(wkf, xor_a)
                if sync != '':
                    S += [sync]
                P  = []
                P += ['P_{0}'.format(xor_b.name)]
                P += ['=']
                P += ['({0}, r_XOR)'.format(xor_b.name)]
                P += ['.']
                node = xor_b.sucessors[0]

            elif node.type == 'OR':
                raise Exception("OR operator not supported!")

        AND_B = node
        P += ['({0}, r_AND)'.format(AND_B.name)]
        P += ['.']
        P += ['P_{0}_{1}'.format(AND_A.name, suc.name)]

        branch = '{0};'.format(' '.join(P))
        wkf.pepa['branches'] += [branch]

    join_expr = ' <{0}, {1}> '.format(AND_A.name, AND_B.name)
    sync = join_expr.join(S)

    AND_B.type = 'AND'
    return (AND_B, sync)

def traverse_XOR(wkf, XOR_A):
    # 'wkf' = current Workflow()
    # 'XOR_A' = Node() of type XOR
    # 'caller' = line within which this function was called

    # Write the beginning of the master XOR line
    S  = []
    P  = []
    P += ['P_{0}'.format(XOR_A.name)]
    P += ['=']

    probsum = 0.0
    sucs = XOR_A.sucessors
    for suc in sucs:
        P += ['({0}, r_{0}_{1})'.format(XOR_A.name, suc.name)]
        P += ['.']
        P += ['P_{0}_{1}'.format(XOR_A.name, suc.name)]
        P += ['+']

        edge = wkf.edges[(XOR_A.name, suc.name)]

        probsum += edge.prob

        prob = 'prob_{0}_{1} = {2};'.format(XOR_A.name, suc.name, edge.prob)
        rate = 'r_{0}_{1} = prob_{0}_{1} * r_XOR;'.format(XOR_A.name, suc.name)

        wkf.pepa['probs'] += [prob]
        wkf.pepa['xor_rates'] += [rate]
        # Write the beginning of each line within the XOR
        Q  = []
        Q += ['P_{0}_{1}'.format(XOR_A.name, suc.name)]
        Q += ['=']

        node = suc
        while len(node.predecessors) == 1:
            if node.type == 'ACT':
                Q += ['({0}, r_{0})'.format(node.name)]
                Q += ['.']

                wkf.pepa['act_rates'] += ['r_{0} = {1};'.format(node.name, node.rate)]
                node = node.sucessors[0]

            elif node.type == 'AND':
                and_a = node
                Q += ['({0}, r_AND)'.format(and_a.name)]
                Q += ['.']

                and_b, sync = traverse_AND(wkf, and_a)
                S += ['<{0}, {1}>'.format(and_a.name, and_b.name)]
                S += ['(' + sync + ')']

                Q += ['({0}, r_AND)'.format(and_b.name)]
                Q += ['.']

                node = and_b.sucessors[0]

            elif node.type == 'XOR':
                xor_a = node

                Q += ['P_{0}'.format(xor_a.name)]

                branch = '{0};'.format(' '.join(Q))
                wkf.pepa['branches'] += [branch]

                xor_b, sync = traverse_XOR(wkf, xor_a)
                if sync != '':
                    S += [sync]
                Q  = []
                Q += ['P_{0}'.format(xor_b.name)]
                Q += ['=']
                Q += ['({0}, r_XOR)'.format(xor_b.name)]
                Q += ['.']

                node = xor_b.sucessors[0]

            elif node.type == 'OR':
                raise Exception("OR operator not supported!")

        XOR_B = node
        Q += ['P_{0}'.format(XOR_B.name)]

        branch = '{0};'.format(' '.join(Q))
        wkf.pepa['branches'] += [branch]

    P.pop()

    branch = '{0};'.format(' '.join(P))
    wkf.pepa['branches'] += [branch]

    if abs(1.0 - probsum) > 1e-6:
        print("Warning: the sum of probabilities of {0} is {1}!".format(XOR_A.name, probsum))

    sync = ' '.join(S)
    XOR_B.type = 'XOR'
    return (XOR_B, sync)

def traverse(wkf, node):
    P  = []
    P += ['P']
    P += ['=']

    S  = []
    S += ['P']

    while len(node.sucessors) > 0:
        if node.type == 'ACT':
            P += ['({0}, r_{0})'.format(node.name)]
            P += ['.']

            wkf.pepa['act_rates'] += ['r_{0} = {1};'.format(node.name, node.rate)]
            node = node.sucessors[0]

        elif node.type == 'AND':
            and_a = node
            P += ['({0}, r_AND)'.format(and_a.name)]
            P += ['.']

            and_b, sync = traverse_AND(wkf, and_a)
            S += [' <{0}, {1}> '.format(and_a.name, and_b.name) + '(' + sync + ')']
            P += ['({0}, r_AND)'.format(and_b.name)]
            P += ['.']

            if len(and_b.sucessors) == 0:
                P += ['P']

                branch = '{0};'.format(' '.join(P))
                wkf.pepa['master'] = branch

                wkf.pepa['sync'] = S
                return
            else:
                node = and_b.sucessors[0]

        elif node.type == 'XOR':
            xor_a = node
            P += ['P_{0}'.format(xor_a.name)]

            branch = '{0};'.format(' '.join(P))
            wkf.pepa['master'] = branch

            xor_b, sync = traverse_XOR(wkf, xor_a)
            if sync != '':
                S += [sync]
            P  = []
            P += ['P_{0}'.format(xor_b.name)]
            P += ['=']

            if len(xor_b.sucessors) == 0:
                P += ['({0}, r_XOR)'.format(xor_b.name)]
                P += ['.']
                P += ['P']

                branch = '{0};'.format(' '.join(P))
                wkf.pepa['branches'] += [branch]

                wkf.pepa['sync'] = S
                return
            else:
                node = xor_b.sucessors[0]

        elif node.type == 'OR':
            raise Exception("OR operator not supported!")

    P += ['({0}, r_{0})'.format(node.name)]
    P += ['.']
    P += ['P']

    rate = 'r_{0} = {1};'.format(node.name, node.rate)
    wkf.pepa['act_rates'] += [rate]

    branch = '{0};'.format(' '.join(P))
    if (wkf.pepa['master'] == ''):
        wkf.pepa['master'] = branch
    else:
        wkf.pepa['branches'] += [branch]

    wkf.pepa['sync'] = S

def solve_pepa(pepa):
    sol = []

    pargs = {"modelstring": pepa, "solver" : "direct"}
    pm = PEPAModel(**pargs)
    pm.steady_state()

    vector = pm.get_steady_state_vector()
    states = pm.get_state_names()

    sol += ["Probabilities of the system's steady states:"]
    for i in range(0, len(vector)):
        sol += [states[i] + '\n' + str(vector[i]) + '\n']
    sol += ['\n']

    # Get throughput of the model's activities
    thrs = pm.get_throughput()
    sol += ["Activities throughput:"]
    for (act, thr) in thrs:
        sol += [act + '\t' + str(thr)]
    sol += ['\n']

    # Get the utilization of each component of the model
    uts = pm.get_utilisations()
    sol += ["Activities utilizations:"]
    for ut in uts:
        sol += ['\nCounter:']
        for item in ut.items():
            sol += [str(item[0]) + '\t' + str(item[1])]

    sol = '\n'.join(sol)
    return sol

if __name__ == '__main__':
    main()
