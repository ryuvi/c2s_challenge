import argparse

def run_server():
    from server.server import Server
    server = Server()
    server.run()

def run_client():
    from client.app import ChatApp
    app = ChatApp()
    app.run()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sistema de busca de veículos')
    parser.add_argument('--server', action='store_true', help='Executa o servidor')
    parser.add_argument('--client', action='store_true', help='Executa o cliente')
    
    args = parser.parse_args()
    
    if args.server:
        run_server()
    elif args.client:
        run_client()
    else:
        print("Por favor, especifique --server ou --client")