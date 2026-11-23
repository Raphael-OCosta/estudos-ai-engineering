"""Dados fictícios usados na trilha prática (todos criados para este curso).

O projeto que atravessa o curso é o **assistente de suporte da Nimbus**, uma empresa (inventada) que vende um
aplicativo de gestão de tarefas para equipes. Aqui estão:

    DOCUMENTOS   -> central de ajuda da Nimbus (base do RAG): lista de dicts {id, titulo, texto}
    PERGUNTAS    -> conjunto de avaliação: pergunta, resposta de referência e id do documento certo
    TICKETS      -> chamados de clientes com a categoria correta (classificação)
    CATEGORIAS   -> categorias possíveis dos chamados
    AVALIACOES   -> comentários de clientes com o sentimento (positivo / negativo / neutro)
"""

DOCUMENTOS = [
    {"id": "planos", "titulo": "Planos e preços",
     "texto": "A Nimbus tem três planos. O plano Grátis permite até 3 usuários e 5 projetos. O plano Equipe custa "
              "R$ 29 por usuário por mês, com projetos ilimitados e relatórios. O plano Empresa custa R$ 59 por "
              "usuário por mês e inclui login único (SSO), registro de auditoria e suporte prioritário. O pagamento "
              "anual dá 20% de desconto."},
    {"id": "cancelamento", "titulo": "Como cancelar a assinatura",
     "texto": "Para cancelar, o administrador acessa Configurações > Assinatura > Cancelar plano. O acesso pago "
              "continua até o fim do período já pago. Não há multa. Os dados ficam disponíveis para exportação por "
              "60 dias após o cancelamento e depois são apagados de forma definitiva."},
    {"id": "reembolso", "titulo": "Política de reembolso",
     "texto": "Pedidos de reembolso são aceitos em até 14 dias após a primeira cobrança de um plano anual. Planos "
              "mensais não têm reembolso proporcional. O reembolso é feito no mesmo meio de pagamento em até 10 dias "
              "úteis depois da aprovação."},
    {"id": "senha", "titulo": "Esqueci minha senha",
     "texto": "Na tela de entrada, clique em Esqueci minha senha e informe o e-mail da conta. O link de troca vale "
              "por 30 minutos. Se a empresa usa SSO, a senha é trocada no provedor de identidade, não na Nimbus. "
              "Depois de 5 tentativas erradas a conta fica bloqueada por 15 minutos."},
    {"id": "integracoes", "titulo": "Integrações disponíveis",
     "texto": "A Nimbus integra com Slack, Microsoft Teams, Google Agenda e GitHub. As integrações são ativadas em "
              "Configurações > Integrações. A integração com o GitHub liga commits às tarefas quando a mensagem do "
              "commit contém o código da tarefa, por exemplo NIM-123."},
    {"id": "exportar", "titulo": "Exportar dados",
     "texto": "Qualquer administrador pode exportar os dados em CSV ou JSON em Configurações > Dados > Exportar. "
              "A exportação inclui tarefas, comentários e anexos e chega por e-mail em até 2 horas. Contas no plano "
              "Grátis exportam apenas CSV."},
    {"id": "limites", "titulo": "Limites de armazenamento",
     "texto": "Cada usuário do plano Equipe tem 10 GB de armazenamento para anexos e cada usuário do plano Empresa "
              "tem 100 GB. O plano Grátis tem 2 GB no total. Arquivos acima de 250 MB não podem ser anexados em "
              "nenhum plano."},
    {"id": "seguranca", "titulo": "Segurança e privacidade",
     "texto": "Os dados ficam em servidores no Brasil, com criptografia em trânsito (TLS 1.3) e em repouso (AES-256). "
              "A Nimbus segue a LGPD e tem um encarregado de dados (DPO) que atende pelo e-mail privacidade@nimbus.exemplo. "
              "A autenticação em dois fatores pode ser exigida para todos os usuários no plano Empresa."},
    {"id": "app_movel", "titulo": "Aplicativo para celular",
     "texto": "O aplicativo da Nimbus existe para Android 10 ou mais recente e iOS 15 ou mais recente. Ele funciona "
              "sem internet para ver e editar tarefas; as mudanças são sincronizadas quando a conexão volta. "
              "Notificações podem ser ajustadas por projeto."},
    {"id": "suporte", "titulo": "Canais de suporte",
     "texto": "O suporte atende por chat de segunda a sexta, das 8h às 20h (horário de Brasília). Clientes do plano "
              "Empresa têm suporte prioritário com resposta em até 2 horas úteis e um gerente de conta. Pedidos fora "
              "do horário são respondidos no próximo dia útil."},
    {"id": "automacoes", "titulo": "Automações",
     "texto": "Automações executam ações quando algo acontece, por exemplo mover a tarefa para Concluído quando "
              "todas as subtarefas terminam. O plano Equipe permite 50 execuções de automação por mês por usuário e "
              "o plano Empresa é ilimitado. O plano Grátis não tem automações."},
    {"id": "convites", "titulo": "Convidar pessoas",
     "texto": "Administradores convidam pessoas em Equipe > Convidar, informando os e-mails. Convidados externos "
              "(visitantes) podem comentar e ver projetos compartilhados, não contam como usuários pagos e não "
              "podem criar projetos. O convite expira em 7 dias."},
]

PERGUNTAS = [
    {"pergunta": "Quanto custa o plano Equipe?", "referencia": "R$ 29 por usuário por mês.", "doc": "planos"},
    {"pergunta": "Tem desconto se eu pagar por ano?", "referencia": "Sim, 20% de desconto no pagamento anual.", "doc": "planos"},
    {"pergunta": "Quantos usuários posso ter no plano grátis?", "referencia": "Até 3 usuários.", "doc": "planos"},
    {"pergunta": "Se eu cancelar, perco meus dados na hora?", "referencia": "Não. Os dados ficam disponíveis para exportação por 60 dias.", "doc": "cancelamento"},
    {"pergunta": "Existe multa para cancelar?", "referencia": "Não há multa.", "doc": "cancelamento"},
    {"pergunta": "Consigo reembolso de um plano mensal?", "referencia": "Não, planos mensais não têm reembolso proporcional.", "doc": "reembolso"},
    {"pergunta": "Em quanto tempo o reembolso cai na conta?", "referencia": "Em até 10 dias úteis após a aprovação.", "doc": "reembolso"},
    {"pergunta": "Por quanto tempo vale o link de troca de senha?", "referencia": "30 minutos.", "doc": "senha"},
    {"pergunta": "Errei a senha várias vezes e fui bloqueado. E agora?", "referencia": "A conta fica bloqueada por 15 minutos após 5 tentativas erradas.", "doc": "senha"},
    {"pergunta": "Como ligo meus commits às tarefas?", "referencia": "Ativando a integração com o GitHub e colocando o código da tarefa (ex.: NIM-123) na mensagem do commit.", "doc": "integracoes"},
    {"pergunta": "A Nimbus funciona com o Teams?", "referencia": "Sim, há integração com o Microsoft Teams.", "doc": "integracoes"},
    {"pergunta": "Posso exportar em JSON no plano grátis?", "referencia": "Não, o plano Grátis exporta apenas CSV.", "doc": "exportar"},
    {"pergunta": "Qual o tamanho máximo de um anexo?", "referencia": "250 MB.", "doc": "limites"},
    {"pergunta": "Onde ficam armazenados os dados?", "referencia": "Em servidores no Brasil, com criptografia.", "doc": "seguranca"},
    {"pergunta": "O app funciona sem internet?", "referencia": "Sim, dá para ver e editar tarefas offline e sincronizar depois.", "doc": "app_movel"},
    {"pergunta": "Qual o horário do suporte?", "referencia": "Segunda a sexta, das 8h às 20h (Brasília).", "doc": "suporte"},
    {"pergunta": "Quantas automações o plano Equipe permite?", "referencia": "50 execuções por mês por usuário.", "doc": "automacoes"},
    {"pergunta": "Visitante conta como usuário pago?", "referencia": "Não, visitantes não contam como usuários pagos.", "doc": "convites"},
]

CATEGORIAS = ["cobranca", "acesso", "bug", "duvida", "cancelamento"]

TICKETS = [
    ("Fui cobrado duas vezes este mês, podem verificar?", "cobranca"),
    ("A fatura veio com valor diferente do plano que contratei.", "cobranca"),
    ("Quero trocar o cartão de crédito da assinatura.", "cobranca"),
    ("Preciso da nota fiscal de março.", "cobranca"),
    ("Não consigo entrar, diz que minha conta está bloqueada.", "acesso"),
    ("O link de redefinir senha não chega no meu e-mail.", "acesso"),
    ("Meu colega não recebeu o convite para a equipe.", "acesso"),
    ("O login com SSO dá erro 403 desde ontem.", "acesso"),
    ("Quando arrasto uma tarefa no quadro, a página trava.", "bug"),
    ("O aplicativo do Android fecha sozinho ao abrir um anexo.", "bug"),
    ("As notificações estão duplicadas no Slack.", "bug"),
    ("O relatório de horas mostra datas erradas.", "bug"),
    ("Vocês têm integração com o Google Agenda?", "duvida"),
    ("Como faço para criar uma automação?", "duvida"),
    ("Qual a diferença entre o plano Equipe e o Empresa?", "duvida"),
    ("Dá para usar a Nimbus sem internet?", "duvida"),
    ("Quero cancelar minha assinatura.", "cancelamento"),
    ("Como encerro a conta da empresa? Vamos migrar de ferramenta.", "cancelamento"),
    ("Não vamos renovar o plano anual, o que acontece com os dados?", "cancelamento"),
    ("Por favor, desativem nossa conta no fim do mês.", "cancelamento"),
]

AVALIACOES = [
    ("Mudou a organização da minha equipe, recomendo muito!", "positivo"),
    ("O app de celular é rápido e funciona até no metrô.", "positivo"),
    ("Suporte respondeu em 10 minutos e resolveu tudo.", "positivo"),
    ("Integração com o GitHub economiza horas por semana.", "positivo"),
    ("Caro para equipes pequenas e o plano grátis é muito limitado.", "negativo"),
    ("Desde a última atualização o quadro ficou lento.", "negativo"),
    ("Perdi um anexo importante e ninguém soube explicar.", "negativo"),
    ("As notificações duplicadas estão me enlouquecendo.", "negativo"),
    ("Uso há dois meses, ainda estou me acostumando.", "neutro"),
    ("Parecido com outras ferramentas do mercado.", "neutro"),
    ("Mudamos do plano Equipe para o Empresa este mês.", "neutro"),
    ("Tem coisas boas e coisas que poderiam melhorar.", "neutro"),
]
