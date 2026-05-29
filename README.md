# Sistema de Transferência de Arquivos P2P

Este repositório contém a implementação de um protocolo de transferência de arquivos Peer-to-Peer (P2P) desenvolvido em Python para a disciplina de Sistemas Distribuídos do CEFET-MG. 

O projeto simula uma rede descentralizada onde os nós (Peers) atuam como clientes e servidores, lidando com a fragmentação, o tráfego e a remontagem de arquivos de diferentes tamanhos com garantia de integridade estrutural.

## 🚀 Principais Funcionalidades

* **Simetria de Rede:** Uso de `threading` para manter o programa principal vivo enquanto *threads* separadas escutam as conexões externas (Servidor) e buscam blocos em vizinhos (Cliente) simultaneamente.
* **Comunicação Confiável:** Utilização de Sockets TCP para garantir a entrega e a ordem dos pacotes de dados.
* **Protocolo de Mensagens:** As requisições e respostas são padronizadas em JSON, e os dados binários dos fragmentos de arquivos são transmitidos com segurança através de codificação Base64.
* **Fragmentação Configurável:** Suporte a diferentes topologias de rede e tamanhos de fragmentação de arquivos (ex: blocos de 1 KB ou 4 KB).
* **Validação de Integridade:** Ao finalizar a remontagem local, o nó receptor calcula o Hash Criptográfico (SHA-256) do novo arquivo e o compara com a assinatura original contida nos metadados, atestando matematicamente que não houve perda de pacotes.

## 🛠️ Pré-requisitos

Para executar os testes locais, você precisará apenas do **Python 3.x** instalado na sua máquina, pois o projeto utiliza exclusivamente bibliotecas nativas da linguagem (`socket`, `threading`, `json`, `hashlib`, `base64`).

## 💻 Como Executar

O sistema pode ser testado no seu ambiente local (localhost) simulando diferentes cenários abrindo múltiplos terminais. Abaixo estão os comandos para rodar os dois cenários principais abordados nos estudos de caso.

### Cenário 1: Configuração Base (2 Peers)
Este cenário testa a transferência direta (1 para 1).

1. Abra um terminal e inicie o nó de origem do arquivo (Seeder):
```python nome_arquivo.py seeder```

2. Abra um segundo terminal e inicie o nó receptor (Leecher):
```python nome_arquivo.py leecher```

### Cenário 2: Efeito Cascata (4 Peers)
Este cenário avalia o comportamento da rede descentralizada em fila, onde um nó requisita blocos e simultaneamente os fornece ao próximo.

Abra 4 terminais diferentes e execute os comandos nesta ordem:

1. Terminal 1 (Transmissor inicial):
```python nome_arquivo.py peer1```

2. Terminal 2 (Baixa do Peer 1 e serve ao Peer 3):
```python nome_arquivo.py peer2```

3. Terminal 3 (Baixa do Peer 2 e serve ao Peer 4):
```python nome_arquivo.py peer3```

4. Terminal 4 (Baixa do Peer 3):
```python nome_arquivo.py peer4```
