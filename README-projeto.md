# Desvie dos Meteoros

Jogo 2D em Python e Pygame para o Trabalho 2 de Programação 2. Escolha entre o
Modelo Arcade, com dificuldade crescente, e o Modo Fases, uma campanha de
viagens entre planetas. O recorde e as fases liberadas ficam salvos em
`save.json` e continuam disponíveis quando o jogo é aberto novamente.
São seis viagens pelos sete planetas, começando na Terra.

## Como executar

Requer Python 3.10 ou superior. O projeto usa pygame-ce, uma distribuição
compatível com o módulo `pygame` e com wheels para Python 3.14. No terminal,
dentro desta pasta:

```powershell
py -m pip install -r requirements.txt
py meteoros.py
```

## Controles

- Setas ou WASD: mover a nave.
- Menu inicial: setas ou A/D selecionam um dos dois modos; Enter ou Espaço inicia.
- Seleção de fases: use as setas ou A/D para escolher entre as fases liberadas;
  pressione Enter para iniciar a viagem selecionada.
- Enter ou Espaço: tentar novamente ou avançar após concluir uma fase.
- Esc: pausar/continuar; nos menus, sair.

## Organização do código

- `meteoros.py`: janela, menus, dois modos de jogo, planetas, movimento,
  surgimento de meteoros, colisão e desenho.
- `carregar_progresso` e `salvar_progresso`: leitura e gravação do recorde Arcade
  e da maior fase liberada em JSON, no mesmo diretório do jogo.
- `requirements.txt`: dependência Pygame.
- `Images/`: imagens dos sete planetas e folhas com três sprites de meteoro para
  cada uma das quatro primeiras viagens. As viagens 5 e 6 usam meteoros
  provisórios desenhados pelo jogo até receberem suas artes. Os fundos brancos
  das imagens são removidos ao carregar os sprites.

No Modo Fases, cada viagem vai de um planeta ao próximo. Cada fase gera uma
quantidade fixa de meteoros, indicada pela barra; é preciso desviar de todos e
esperar que saiam da tela para concluir e liberar a próxima. A moldura branca
destaca a opção ou fase selecionada; a navegação para nas fases liberadas.
Para demonstrar a manutenção de estado no vídeo, conclua uma fase, feche e abra
o jogo novamente: a seleção deve manter as fases liberadas. O Arcade troca de
planeta e conjunto visual de meteoros a cada 25 segundos, aumenta a dificuldade
ao longo da partida e os meteoros giram enquanto caem.
