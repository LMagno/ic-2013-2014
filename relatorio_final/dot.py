def dot_pdf(wkf):
  # Descrever o workflow em linguagem DOT, gerar sua visualização
  # e salvar ambas em arquivos de saída
  
  # Obter string com a descrição do workflow em linguagem DOT
  dot = write(wkf)

  # Escrevê-la num arquivo de saída
  with open(wkf.name + '.dot', 'w') as f:
    f.write(dot)
  
  # Renderizar workflow baseado em sua descrição em DOT
  # e salvar em um arquivo pdf
  gvv = gv.readstring(dot)
  gv.layout(gvv,'dot')
  gv.render(gvv,'pdf', wkf.name + '.pdf')