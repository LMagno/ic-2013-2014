## Resumo
As atividades aqui descritas foram desenvolvidas durante o período de julho de 2013 a junho de 2014 no âmbito do projeto de iniciação científica do aluno Lucas Magno, orientado pela Profa. Dra. Kelly Rosa Braghetto e financiado por uma bolsa PIBIC/CNPq.

O objetivo principal do projeto foi desenvolver uma ferramenta de software para a conversão automática de modelos de *workflows* em modelos estocásticos na álgebra de processos *PEPA - Performance Evaluation Process Algebra*. A partir desses modelos estocásticos, é possível extrair predições de desempenho de *workflows*.

## O Programa
Para automatizar o processo de predição de desempenho, foi implementado um programa
que realiza as seguintes etapas:

1. Lê como entrada uma descrição textual de um workflow
2. Gera uma estrutura de dados baseada em grafo na memória representando o workflow
3. Gera uma visualização do workflow de entrada
4. Gera um modelo analítico (estocástico) do workflow
5. Solução numérica do modelo analítico e extração dos índices de desempenho

### Dependências
Em um sistema linux baseado em Debian, os seguintes pacotes devem ser instalados além da
instalação padrão do python 2.7:
* python-ply (Biblioteca Python Lex-Yacc)
* libgv-python (Biblioteca Graphviz)
* python-pyparsing (Biblioteca pyParsing)
* python-numpy (Biblioteca NumPy)
* python-scipy (Biblioteca SciPy)

Além disso, a biblioteca [pyPEPA](https://github.com/tdi/pyPEPA) também deve ser instalada.

### Execução
O programa deve ser executado a partir de um terminal utilizando os seguintes comandos:

    python script.py input1 input2 input3

Onde *script.py* é o arquivo que contém o programa,
e *input1*, *input2* e *input3* são arquivos de entrada contendo descrições textuais de *workflows* na
linguagem definida neste projeto. Não há limite para a quantidade de arquivos de entrada.

O programa então processa os workflows e, caso não haja erros, imprime para a tela:

    workflow1 was sucessfully processed! :D
    Output files were created.

E cria os seguintes arquivos de saída:
* workflow1.dot
* workflow1.pdf
* workflow1.pepa
* workflow1_solution

No caso de ocorrerem erros no processamento de um *workflow*, a seguinte mensagem será
impressa para a tela:

    There was an error while processing workflow1. :(
    Traceback was logged to "workflow1_traceback".

Onde *workflow1_traceback* é um arquivo contendo a mensagem de erro originalmente produzida, que não foi impressa para a tela para não a poluir. Também podem ser criados alguns arquivos de saída, dependendo do local do código onde o erro ocorreu.

Deve-se notar que o processamento de cada *workflow* é feito de forma independente, ou seja, essas mensagens serão impressas para cada *workflow* processado e a ocorrência de erro em um processamente não interfere em nada no próximo.
