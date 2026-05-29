import socket
import threading
import json
import os
import hashlib
import time
import base64
from datetime import datetime

class Peer:
    def __init__(self, host, port, neighbors_list, block_size=1024):
        self.host = host
        self.port = port
        self.neighbors = neighbors_list # Configuração estática de vizinhos
        self.block_size = block_size    # Tamanho do bloco: 1024 Bytes (1 KB)
        
        self.blocks_owned = {}          
        self.metadata = None            
        self.file_complete = False

    def log(self, tag, message):
        """Padroniza as mensagens no terminal com a hora exata."""
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"[{current_time}] [{tag}] {message}")

    # ==========================================
    # LADO SERVIDOR (SEEDER)
    # ==========================================
    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        self.log("Servidor", f"Ouvindo em {self.host}:{self.port}")

        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr)).start()

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                return
            
            request = json.loads(data)
            
            if request['action'] == 'REQUEST_META':
                if self.metadata:
                    response = {'status': 'OK', 'metadata': self.metadata}
                else:
                    response = {'status': 'ERROR', 'msg': 'Sem metadados'}
                conn.send(json.dumps(response).encode('utf-8'))
            
            elif request['action'] == 'REQUEST_BLOCK':
                block_idx = request['block_index']
                if block_idx in self.blocks_owned:
                    encoded_data = base64.b64encode(self.blocks_owned[block_idx]).decode('utf-8')
                    response = {'status': 'OK', 'block_index': block_idx, 'data': encoded_data}
                    
                    # LÓGICA DE LOG RESUMIDO (SERVIDOR)
                    if block_idx == 0:
                        self.log("Servidor", f"Enviou bloco {block_idx} para {addr}")
                    elif block_idx == 1:
                        self.log("Servidor", "...")
                    elif block_idx == self.metadata['total_blocks'] - 1:
                        self.log("Servidor", f"Enviou bloco {block_idx} para {addr}")

                else:
                    response = {'status': 'ERROR', 'msg': 'Bloco não encontrado'}
                    self.log("Servidor", f"Pedido de bloco {block_idx} indisponível de {addr}")
                    
                conn.send(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            pass
        finally:
            conn.close()

    # ==========================================
    # LADO CLIENTE (LEECHER)
    # ==========================================
    def start_client(self):
        while not self.file_complete:
            for neighbor_ip, neighbor_port in self.neighbors:
                if not self.metadata:
                    self.fetch_metadata(neighbor_ip, neighbor_port)
                else:
                    self.fetch_missing_blocks(neighbor_ip, neighbor_port)
            
            if self.metadata and len(self.blocks_owned) == self.metadata['total_blocks']:
                self.file_complete = True
                self.assemble_file()
            else:
                time.sleep(1)

    def fetch_metadata(self, ip, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            req = json.dumps({'action': 'REQUEST_META'}).encode('utf-8')
            s.send(req)
            
            resp = json.loads(s.recv(4096).decode('utf-8'))
            if resp['status'] == 'OK':
                self.metadata = resp['metadata']
                self.log("Leecher", f"Metadado carregado de {self.metadata['filename']}")
                self.log("Leecher", f"Esperando {self.metadata['total_blocks']} blocos ({self.block_size} bytes cada).")
            s.close()
        except:
            pass

    def fetch_missing_blocks(self, ip, port):
        for i in range(self.metadata['total_blocks']):
            if i not in self.blocks_owned:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect((ip, port))
                    req = json.dumps({'action': 'REQUEST_BLOCK', 'block_index': i}).encode('utf-8')
                    s.send(req)
                    
                    raw_data = s.recv(1024 * 50) 
                    resp = json.loads(raw_data.decode('utf-8'))
                    
                    if resp['status'] == 'OK':
                        block_data = base64.b64decode(resp['data'])
                        self.blocks_owned[i] = block_data
                        
                        # LÓGICA DE LOG RESUMIDO (CLIENTE)
                        if i == 0:
                            self.log("Cliente", f"Recebeu bloco {i} de {ip}:{port}")
                        elif i == 1:
                            self.log("Cliente", "...")
                        elif i == self.metadata['total_blocks'] - 1:
                            self.log("Cliente", f"Recebeu bloco {i} de {ip}:{port}")
                    s.close()
                except:
                    pass

    # ==========================================
    # MANIPULAÇÃO DE ARQUIVOS
    # ==========================================
    def fragment_file(self, filepath):
        if not os.path.exists(filepath):
            return

        file_size = os.path.getsize(filepath)
        sha256_hash = hashlib.sha256()

        with open(filepath, 'rb') as f:
            sha256_hash.update(f.read())
        
        original_hash = sha256_hash.hexdigest()

        with open(filepath, 'rb') as f:
            block_index = 0
            while True:
                data = f.read(self.block_size)
                if not data:
                    break
                self.blocks_owned[block_index] = data
                block_index += 1

        self.metadata = {
            'filename': os.path.basename(filepath),
            'filesize': file_size,
            'total_blocks': block_index,
            'original_hash': original_hash
        }
        self.file_complete = True
        self.log("Fragmentador", f"Arquivo original fragmentado em {block_index} blocos.")

    def assemble_file(self):
        output_filename = f"ArquivoBaixadoPeloPort_{self.port}_{self.metadata['filename']}"
        
        with open(output_filename, 'wb') as f:
            for i in range(self.metadata['total_blocks']):
                f.write(self.blocks_owned[i])
        
        sha256_hash = hashlib.sha256()
        with open(output_filename, 'rb') as f:
            sha256_hash.update(f.read())
            
        new_hash = sha256_hash.hexdigest()
        
        self.log("Peer", f"Arquivo final salvo como {output_filename}")
        self.log("Peer", "Download completo!")
        self.log("Checksum", f"Hash Original: {self.metadata['original_hash']}")
        self.log("Checksum", f"Hash Recebido: {new_hash}")
        
        if new_hash == self.metadata['original_hash']:
            self.log("Integridade", "Arquivo verificado com sucesso (SHA-256 idêntico ao metadado).")
        else:
            self.log("Integridade", "FALHOU! Hash incompatível.")
        print("-" * 50)

    # ==========================================
    # INICIALIZAÇÃO E TESTE (FILE C)
    # ==========================================
    def run(self):
        self.log("Inicialização", f"Peer iniciado em {self.host}:{self.port}")
        self.log("Config", f"Vizinhos configurados estaticamente: {self.neighbors}")

        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()

        client_thread = threading.Thread(target=self.start_client)
        client_thread.daemon = True
        client_thread.start()

        while True:
            time.sleep(1)

if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "leecher"

    if mode == "seeder":
        # 1. Criação do Arquivo Grande (File C) com exatamente 10 MB (10 * 1024 * 1024 bytes)
        with open("file_C_10MB.txt", "wb") as f:
            f.write(os.urandom(10 * 1024 * 1024)) 

        # 2. Configuração: 2 Peers, Bloco de 1024 bytes (1 KB)
        peer1 = Peer('127.0.0.1', 5000, [('127.0.0.1', 5001)], block_size=1024)
        peer1.fragment_file("file_C_10MB.txt")
        peer1.run()

    elif mode == "leecher":
        # 3. Configuração do 2º Peer (Ouvindo na 5001, vizinho na 5000 pedindo o arquivo)
        peer2 = Peer('127.0.0.1', 5001, [('127.0.0.1', 5000)], block_size=1024)
        peer2.run()
    else:
        print("Uso correto: py peer_file_C.py [seeder|leecher]")