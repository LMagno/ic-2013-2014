from pypepa import PEPAModel

# Abre o arquivo .pepa e le o modelo contido nele
pargs = {"file": "workflow1.pepa", "solver" : "direct"}
#pargs = {"file": "ex_relatorio.pepa", "solver" : "sparse"}
pm = PEPAModel(**pargs)
pm.steady_state()


# Calcula o vetor de probabilidades dos estados do
# sistema no regime estacionario
vector = pm.get_steady_state_vector()
# Obtem os nomes dos estados
states = pm.get_state_names()
print("Probabilidades dos estados do sistema no regime estacionario: ")
print(list(zip(states,vector)))

# Obtem o rendimento (throughput) das atividades do modelo
thr = pm.get_throughput()
print("Rendimento das atividades: ")
print(thr)

# Obtem a utilizacao de cada componente do modelo
uts = pm.get_utilisations()
print("Utilizacao dos componentes: ")
print(uts)