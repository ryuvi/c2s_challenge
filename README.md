# 🚗 Sistema de Busca de Veículos - Challenge C2S

## 📋 Visão Geral

Sistema completo de busca de veículos com:

- **Backend**: Servidor Python com ZMQ (ZeroMQ), SQLAlchemy, Pandas e Dotenv
- **Frontend**: Interface terminal (TUI) com Textual e ZMQ (Comunicação com backend)
- **Banco de Dados**: PostgreSQL (container) ou SQLite (local)

## ▶️ Como Executar

### Pré-requisitos

- Python 3.9+
- Podman ou Docker (opcional para PostgreSQL)

### Método Principal (Recomendado)

```bash
# 1. Crie um ambiente virtual
python -m venv venv

# 2. Ative o venv
./venv/bin/activate # Linux
./venv/Scripts/activate # Windows

# 3. Instale as dependencias
pip install -r requirements.txt

# 4. Inicie o servidor (em um terminal)
python main.py --server

# 5. Inicie o client (em outro terminal)
python main.py --client
```



### Opção com PostgreSQL via Container

```bash
# 1. Suba o container do PostgreSQL e serve com compose
podman compose --file "docker-compose.yaml" up --detach

# 2. Execute o client normalmente
python main.py --client
```

## ⚙️ Configuração

O sistema funciona imediatamente com SQLite. Para PostgreSQL:

1. Crie/copie o arquivo `.env`:
   
   ```ini
   DB_TYPE=postgresql
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=cars
   DB_USER=admin
   DB_PASSWORD=admin
   ```

2. Ou use SQLite (padrão):
   
   ```ini
   DB_TYPE=sqlite
   DB_NAME=cars
   ```

## 🖥️ Interface do Sistema

![Screenshot da Interface](img/client.png) 

### Atalhos:

- `Ctrl+Q`: Sair do sistema
- `Enter`: Enviar mensagem
- Botão `Enviar`: Alternativa para envio

## 🔄 Reset do Sistema

Para reiniciar o estado da conversa:

1. Pressione `Ctrl+C` no servidor
2. Execute novamente:
   
   ```bash
   python -m server.server
   ```

## ## 📌 Observações

- O banco é automaticamente populado com dados fictícios na primeira execução
- O sistema foi testado no Windows apenas.