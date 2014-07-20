import gv
import sys
import ply.lex as lex
import ply.yacc as yacc
import pygraph.mixins.labeling
from pygraph.readwrite.dot import write
from pygraph.classes.digraph import digraph

# Lista de tokens
reserved = {
	'digraph' : 'DIGRAPH', 
	'OR' : 'OR',
	'XOR' : 'XOR',
	'AND' : 'AND'
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
	'SEMICOLON'
] + list(reserved.values())

# Regras de expressão regular para tokens simples
t_OPEN_BRACE = r'\{'
t_CLOSE_BRACE = r'\}' 
t_OPEN_BRACKET = r'\['
t_CLOSE_BRACKET = r'\]'
t_EDGEOP = r'->'
t_COMMA = r','
t_SEMICOLON = r';'

# Regras de expressões regulares com alguma ação
def t_ID(t):
	r'[a-zA-Z_][a-zA-Z_0-9]*'
	t.type = reserved.get(t.value, 'ID')
	return t

def t_NUMBER(t):
	r'\d+\.\d+|\d+'
	t.value = float(t.value)
	return t

# Definir uma regra pra registrar o número de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Uma string contendo caracteres ignorados (espaços e tabs)
t_ignore  = ' \t'

# Regra para tratamento de erro
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.lexer.skip(1)

# Compilar o analisador léxico
lexer = lex.lex()

# Obter dados do arquivo
arq = open(sys.argv[1], "r")
data = arq.read()

# Dar uma entrada para o analisador léxico
lexer.input(data)

# Criar o digrafo
dgr = digraph()

# Expressões do analisador sintático

# Definir nome do digrafo e o atribuir à variável global 'dgrname' 
def p_digraph_id(t):
	'digraph : DIGRAPH ID OPEN_BRACE stmt CLOSE_BRACE'
	global dgrname
	dgrname = t[2]

def p_digraph_no_id(t):
	'digraph : DIGRAPH OPEN_BRACE stmt CLOSE_BRACE'
	global dgrname
	dgrname = 'workflow'


def p_stmtlist(t):
	'stmt : stmt stmt'

# Criar as arestas
def p_stmt(t):
	'stmt : node edge SEMICOLON'
	for edge in t[2]:
		dgr.add_edge((t[1]['name'], edge['node']), 1, edge['label'])


# Criar cada vértice ou atualizar seus atributos caso este já exista
def p_node_atrr_op_or(t):
	'node : ID OPEN_BRACKET OR CLOSE_BRACKET EDGEOP'
	t[0] = {'name': t[1], 'attr': 'OR'}
	if dgr.has_node(t[1]):
		dgr.add_node_attribute(t[1], ('attr', 'OR'))
		dgr.add_node_attribute(t[1], ('shape', 'diamond'))
	else:
		dgr.add_node(t[1], [('attr', 'OR'), ('shape', 'diamond')])

def p_node_atrr_op_xor(t):
	'node : ID OPEN_BRACKET XOR CLOSE_BRACKET EDGEOP'
	t[0] = {'name': t[1], 'attr': 'XOR'}
	if dgr.has_node(t[1]):
		dgr.add_node_attribute(t[1], ('attr', 'XOR'))
		dgr.add_node_attribute(t[1], ('shape', 'diamond'))
	else:
		dgr.add_node(t[1], [('attr', 'XOR'), ('shape', 'diamond')])

def p_node_atrr_op_and(t):
	'node : ID OPEN_BRACKET AND CLOSE_BRACKET EDGEOP'
	t[0] = {'name': t[1], 'attr': 'AND'}
	if dgr.has_node(t[1]):
		dgr.add_node_attribute(t[1], ('attr', 'AND'))
		dgr.add_node_attribute(t[1], ('shape', 'diamond'))
	else:
		dgr.add_node(t[1], [('attr', 'AND'), ('shape', 'diamond')])

def p_node_attr_num(t):
	'node : ID OPEN_BRACKET NUMBER CLOSE_BRACKET EDGEOP'
	t[0] = {'name': t[1], 'attr': t[3]}
	if dgr.has_node(t[1]):
		dgr.add_node_attribute(t[1], ('attr', t[3]))
		dgr.add_node_attribute(t[1], ('shape', 'box'))
	else:
		dgr.add_node(t[1], [('attr', t[3]), ('shape', 'box')])

def p_node_attr_none(t):
	'node : ID EDGEOP'
	t[0] = {'name': t[1], 'attr': 1.0}
	if dgr.has_node(t[1]):
		dgr.add_node_attribute(t[1], ('attr', 1.0))
		dgr.add_node_attribute(t[1], ('shape', 'box'))
	else:
		dgr.add_node(t[1], [('attr', 1.0), ('shape', 'box')])

def p_edge_list(t):
	'edge : edge COMMA edge'
	t[0] = t[1] + t[3]

# Criar vértices ainda não existentes para
# posteriormente as arestas poderem ser criadas
# Atributos serão adicionados depois
def p_edge_prob(t):
	'edge : OPEN_BRACKET NUMBER CLOSE_BRACKET ID'
	t[0] = [{'node': t[4], 'label': t[2]}]
	if not dgr.has_node(t[4]):
		dgr.add_node(t[4])

def p_edge_no_prob(t):
	'edge : ID'
	t[0] = [{'node': t[1], 'label': 1.0}]
	if not dgr.has_node(t[1]):
		dgr.add_node(t[1])

# Tratamento de erro
def p_error(t):
    print("Syntax error at '%s'" % t.value)

# Compilar o analisador sintático
yacc.yacc()
yacc.parse(data)

# Atualizar vértices sem atributos para equivaler a um vértice padrão
for node in dgr.nodes():
	if dgr.node_attributes(node) == []:
		dgr.add_node_attribute(node, ('attr', 1.0))
		dgr.add_node_attribute(node, ('shape', 'box'))

# Escrever para a linguagem DOT
dot = write(dgr)

# Gravar código em DOT em arquivo externo 
dot_file = open(dgrname + '.dot', 'w')
dot_file.write(dot)
dot_file.close()

# Gravar visualização gráfica em arquivo pdf externo
gvv = gv.readstring(dot)
gv.layout(gvv,'dot')
gv.render(gvv,'pdf', dgrname + '.pdf')