from flask import Flask
from flask import jsonify
from flask import request
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
import sqlite3

app = Flask(__name__)

# ------------------------------------ Configuração do banco de dados ------------------------------------------------------------------
conn = sqlite3.connect('torneio.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS times (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                 nome TEXT,
                                                 localidade TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS jogadores (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                     nome TEXT,
                                                     data_nascimento TEXT,
                                                     pais TEXT,
                                                     time_id INTEGER,
                                                     FOREIGN KEY(time_id) REFERENCES times(id))''')
c.execute('''CREATE TABLE IF NOT EXISTS transferencias (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                                         jogador_id INTEGER,
                                                         time_origem_id INTEGER,
                                                         time_destino_id INTEGER,
                                                         data TEXT,
                                                         valor REAL,
                                                         FOREIGN KEY(jogador_id) REFERENCES jogadores(id),
                                                         FOREIGN KEY(time_origem_id) REFERENCES times(id),
                                                         FOREIGN KEY(time_destino_id) REFERENCES times(id))''')
c.execute('''CREATE TABLE IF NOT EXISTS torneio (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT,
                 localidade TEXT
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS partidas (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 time_casa_id INTEGER,
                 time_visitante_id INTEGER,
                 inicio TEXT,
                 gol_casa INTEGER DEFAULT 0,
                 gol_visitante INTEGER DEFAULT 0,
                 intervalo INTEGER DEFAULT 0,
                 acrescimo INTEGER DEFAULT 0,
                 substituicao TEXT,
                 advertencia TEXT,
                 fim TEXT,
                 FOREIGN KEY(time_casa_id) REFERENCES times(id),
                 FOREIGN KEY(time_visitante_id) REFERENCES times(id)
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS eventos (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 partida_id INTEGER,
                 tipo TEXT,
                 tempo INTEGER,
                 jogador_id INTEGER,
                 FOREIGN KEY(partida_id) REFERENCES partidas(id),
                 FOREIGN KEY(jogador_id) REFERENCES jogadores(id)
             )''')

conn.commit()


# Funções para manipular o banco de dados
def criar_time(nome, localidade):
    c.execute('''INSERT INTO times (nome, localidade) VALUES (?, ?)''', (nome, localidade))
    conn.commit()
    return c.lastrowid

def buscar_time(id):
    c.execute('''SELECT * FROM times WHERE id = ?''', (id,))
    time = c.fetchone()
    if time is None:
        return None
    return {'id': time[0], 'nome': time[1], 'localidade': time[2]}

def criar_jogador(nome, data_nascimento, pais, time_id):
    c.execute('''INSERT INTO jogadores (nome, data_nascimento, pais, time_id) VALUES (?, ?, ?, ?)''',
              (nome, data_nascimento, pais, time_id))
    conn.commit()
    return c.lastrowid

def buscar_jogador(id):
    c.execute('''SELECT * FROM jogadores WHERE id = ?''', (id,))
    jogador = c.fetchone()
    if jogador is None:
        return None
    return {'id': jogador[0], 'nome': jogador[1], 'data_nascimento': jogador[2], 'pais': jogador[3], 'time_id': jogador[4]}

def listar_jogadores():
    c.execute("SELECT j.nome, j.data_nascimento, j.pais, t.nome FROM jogadores j JOIN times t ON j.time_id = t.id")
    jogadores = c.fetchall()
    return jogadores

def criar_transferencia(jogador_id, time_origem_id, time_destino_id, data, valor):
    c.execute('''INSERT INTO transferencias (jogador_id, time_origem_id, time_destino_id, data, valor)
                 VALUES (?, ?, ?, ?, ?)''', (jogador_id, time_origem_id, time_destino_id, data, valor))
    conn.commit()
    return c.lastrowid

def buscar_transferencias_jogador(id):
    c.execute('''SELECT t1.nome as time_origem, t2.nome as time_destino, tr.data, tr.valor
                 FROM transferencias tr
                 JOIN times t1 ON tr.time_origem_id = t1.id
                 JOIN times t2 ON tr.time_destino_id = t2.id
                 WHERE tr.jogador_id = ?''', (id,))
    transferencias = c.fetchall()
    return transferencias

def listar_transferencias():
    c.execute('''SELECT transferencias.id, jogadores.nome, times_origem.nome, times_destino.nome, transferencias.data, transferencias.valor
                 FROM transferencias
                 INNER JOIN jogadores ON transferencias.jogador_id = jogadores.id
                 INNER JOIN times AS times_origem ON transferencias.time_origem_id = times_origem.id
                 INNER JOIN times AS times_destino ON transferencias.time_destino_id = times_destino.id''')

    transferencias = c.fetchall()
    transferencias_list = []

    for t in transferencias:
        transferencia = (t[0], t[1], t[2], t[3], t[4], t[5])
        transferencias_list.append(transferencia)

    return transferencias_list

def criar_torneio(nome, localidade):
    c.execute('''INSERT INTO torneio (nome, localidade) VALUES (?, ?)''', (nome, localidade))
    conn.commit()
    return c.lastrowid

def buscar_torneio(id):
    c.execute('SELECT * FROM torneio WHERE id = ?', (id,))
    torneio = c.fetchone()
    return torneio

def atualizar_torneio(id, nome, data_inicio, data_fim):
    c.execute('''UPDATE torneio SET nome = ?, data_inicio = ?, data_fim = ? WHERE id = ?''',
              (nome, data_inicio, data_fim, id))   
    conn.commit()


def criar_partida(torneio_id, time_casa_id, time_visitante_id, data, local, resultado):
    with sqlite3.connect("database.db") as conn:
        c = conn.cursor()
        c.execute("INSERT INTO partidas (torneio_id, time_casa_id, time_visitante_id, inicio, local, resultado) VALUES (?, ?, ?, ?, ?, ?)",
                  (torneio_id, time_casa_id, time_visitante_id, data, local, resultado))
        conn.commit()
        partida_id = c.lastrowid
        return partida_id
    
def buscar_partidas_torneio(id_torneio):
    conn = sqlite3.connect('caminho/para/o/banco/de/dados')
    c = conn.cursor()
    c.execute('SELECT * FROM partidas WHERE time_casa_id IN (SELECT id FROM times WHERE torneio_id = ?) AND time_visitante_id IN (SELECT id FROM times WHERE torneio_id = ?)', (id_torneio, id_torneio))
    partidas = c.fetchall()
    conn.close()
    return partidas

def listar_partidas():
    c.execute("SELECT * FROM partidas")
    partidas = c.fetchall()
    return partidas   
 
# ------------------------------ Rotas e endpoints da API --------------------------------------------------------------------------------------------------

# Rota para criar um time
@app.route('/time', methods=['POST'])
def criar_time_endpoint():
    nome = request.json['nome']
    localidade = request.json['localidade']
    time_id = criar_time(nome, localidade)
    time = buscar_time(time_id)
    return jsonify(time)

# Rota para buscar um time
@app.route('/time/<int:id>', methods=['GET'])
def buscar_time_endpoint(id):
    time = buscar_time(id)
    if time is None:
        return jsonify({'mensagem': 'Time não encontrado'})
    return jsonify(time)

# Rota para atualizar um time
@app.route('/time/<int:id>', methods=['PUT'])
def atualizar_time_endpoint(id):
    time = buscar_time(id)
    if time is None:
        return jsonify({'mensagem': 'Time não encontrado'})
    
        nome = request.json.get('nome', time['nome'])
        localidade = request.json.get('localidade', time['localidade'])
        atualizar_time(id, nome, localidade)
        
    time_atualizado = buscar_time(id)
    
    return jsonify(time_atualizado)

# Rota para criar um jogador
@app.route('/jogador', methods=['POST'])
def criar_jogador_endpoint():
    nome = request.json['nome']
    data_nascimento = request.json['data_nascimento']
    pais = request.json['pais']
    time_id = request.json['time_id']
    jogador_id = criar_jogador(nome, data_nascimento, pais, time_id)
    jogador = buscar_jogador(jogador_id)
    return jsonify(jogador)

# Rota para buscar um jogador
@app.route('/jogador/<int:id>', methods=['GET'])
def buscar_jogador_endpoint(id):
    jogador = buscar_jogador(id)
    if jogador is None:
        return jsonify({'mensagem': 'Jogador não encontrado'})
    return jsonify(jogador)

# Rota para atualizar um jogador
@app.route('/jogador/<int:id>', methods=['PUT'])
def atualizar_jogador_endpoint(id):
    jogador = buscar_jogador(id)
    if jogador is None:
        return jsonify({'mensagem': 'Jogador não encontrado'})
    
        nome = request.json.get('nome', jogador['nome'])
        data_nascimento = request.json.get('data_nascimento', jogador['data_nascimento'])
        pais = request.json.get('pais', jogador['pais'])
        time_id = request.json.get('time_id', jogador['time_id'])
    
        atualizar_jogador(id, nome, data_nascimento, pais, time_id)
        
    jogador_atualizado = buscar_jogador(id)
    
    return jsonify(jogador_atualizado)

# Rota para listar todos os jogadores
@app.route('/jogadores', methods=['GET'])
def listar_jogadores_endpoint():
    jogadores = listar_jogadores()
    return jsonify(jogadores)

# Rota para criar uma transferência
@app.route('/transferencia', methods=['POST'])
def criar_transferencia_endpoint():
    jogador_id = request.json.get('jogador_id')
    time_origem_id = request.json.get('time_origem_id')
    time_destino_id = request.json.get('time_destino_id')
    data = request.json.get('data')
    valor = request.json.get('valor')
    
    # Verificar se os times e jogadores existem
    jogador = buscar_jogador(jogador_id)
    if jogador is None:
        return jsonify({'erro': 'Jogador não encontrado'}), 404
    time_origem = buscar_time(time_origem_id)
    if time_origem is None:
        return jsonify({'erro': 'Time de origem não encontrado'}), 404
    time_destino = buscar_time(time_destino_id)
    if time_destino is None:
        return jsonify({'erro': 'Time de destino não encontrado'}), 404
    
    # Criar a transferência e retornar os dados da transferência criada
    transferencia_id = criar_transferencia(jogador_id, time_origem_id, time_destino_id, data, valor)
    transferencia = {'id': transferencia_id,
                     'jogador': jogador,
                     'time_origem': time_origem,
                     'time_destino': time_destino,
                     'data': data,
                     'valor': valor}
    return jsonify(transferencia), 201

# Rota para buscar as transferências de um jogador
@app.route('/jogador/<int:id>/transferencias', methods=['GET'])
def buscar_transferencias_jogador_endpoint(id):
    jogador = buscar_jogador(id)
    if jogador is None:
        return jsonify({'mensagem': 'Jogador não encontrado'})
    
    transferencias = buscar_transferencias_jogador(id)
    
    return jsonify(transferencias)

# Rota para listar todas as transferências
@app.route('/transferencias', methods=['GET'])
def listar_transferencias_endpoint():
    transferencias = listar_transferencias()
    return jsonify(transferencias)

# Rota para criar um torneio
@app.route('/torneio', methods=['POST'])
def criar_torneio_endpoint():
    nome = request.json['nome']
    data_inicio = request.json['data_inicio']
    data_fim = request.json['data_fim']
    torneio_id = criar_torneio(nome, data_inicio, data_fim)
    torneio = buscar_torneio(torneio_id)
    return jsonify(torneio)

# Rota para buscar um torneio
@app.route('/torneio/int:id', methods=['GET'])
def buscar_torneio_endpoint(id):
    torneio = buscar_torneio(id)
    if torneio is None:
        return jsonify({'mensagem': 'Torneio não encontrado'})
    return jsonify(torneio)

# Rota para atualizar um torneio
@app.route('/torneio/int:id', methods=['PUT'])
def atualizar_torneio_endpoint(id):
    torneio = buscar_torneio(id)
    if torneio is None:
        return jsonify({'mensagem': 'Torneio não encontrado'})
    
    nome = request.json.get('nome', torneio['nome'])
    data_inicio = request.json.get('data_inicio', torneio['data_inicio'])
    data_fim = request.json.get('data_fim', torneio['data_fim'])

    atualizar_torneio(id, nome, data_inicio, data_fim)
    
    torneio_atualizado = buscar_torneio(id)

    return jsonify(torneio_atualizado)

# Rota para criar uma partida
@app.route('/partida', methods=['POST'])
def criar_partida_endpoint():
    torneio_id = request.json.get('torneio_id')
    time_casa_id = request.json.get('time_casa_id')
    time_visitante_id = request.json.get('time_visitante_id')
    data = request.json.get('data')
    local = request.json.get('local')
    resultado = request.json.get('resultado')

     #Verificar se os times e torneios existem
    torneio = buscar_torneio(torneio_id)
    if torneio is None:
        return jsonify({'erro': 'Torneio não encontrado'}), 404
    time_casa = buscar_time(time_casa_id)
    
    if time_casa is None:
        return jsonify({'erro': 'Time da casa não encontrado'}), 404
    time_visitante = buscar_time(time_visitante_id)
    
    if time_visitante is None:
        return jsonify({'erro': 'Time visitante não encontrado'}), 404

    # Criar a partida e retornar os dados da partida criada
    partida_id = criar_partida(torneio_id, time_casa_id, time_visitante_id, data, local, resultado)
    partida = {'id': partida_id,
            'torneio': torneio,
            'time_casa': time_casa,
            'time_visitante': time_visitante,
            'data': data,
            'local': local,
            'resultado': resultado}
    
    return jsonify(partida), 201

# Rota para buscar as partidas de um torneio
@app.route('/torneio/int:id/partidas', methods=['GET'])
def buscar_partidas_torneio_endpoint(id):
    torneio = buscar_torneio(id)
    if torneio is None:
        return jsonify({'mensagem': 'Torneio não encontrado'})    

    partidas = buscar_partidas_torneio(id)

    return jsonify(partidas)

# Rota para listar todas as partidas
@app.route('/partidas', methods=['GET'])
def listar_partidas_endpoint():
    partidas = listar_partidas()
    return jsonify(partidas)

# Rota para adiconar início da partida
@app.route('/torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/inicio', methods=['POST'])
def inicio_partida(torneio_id, partida_id):
    inicio = request.json['tempo']
    c.execute('UPDATE partidas SET inicio = ? WHERE id = ?', (inicio, partida_id,))
    conn.commit()
    return jsonify({'mensagem': 'Início da partida registrado com sucesso.'})

# Rota para o adicionar Gol
@app.route('/torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/gol', methods=['POST'])
def gol(torneio_id, partida_id):
    gol = request.json['gol']
    time = request.json['time']
    tipo = 'gol_casa' if time == 'casa' else 'gol_visitante'
    c.execute('UPDATE partidas SET {} = {} + 1 WHERE id = ?'.format(tipo, tipo), (partida_id,))
    c.execute('INSERT INTO eventos (partida_id, tipo, tempo) VALUES (?, ?, ?)', (partida_id, 'gol', request.json['tempo'],))
    conn.commit()
    return jsonify({'mensagem': 'Gol registrado com sucesso.'})

# Rota para adicionar intervalo
@app.route('/torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/intervalo', methods=['POST'])
def intervalo(torneio_id, partida_id):
    intervalo = request.json['tempo']
    c.execute('UPDATE partidas SET intervalo = ? WHERE id = ?', (intervalo, partida_id,))
    c.execute('INSERT INTO eventos (partida_id, tipo, tempo) VALUES (?, ?, ?)', (partida_id, 'intervalo', request.json['tempo'],))
    conn.commit()
    return jsonify({'mensagem': 'Intervalo registrado com sucesso.'})

# Rota para adicionar acréscimo
@app.route('/torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/acrescimo', methods=['POST'])
def acrescimo(torneio_id, partida_id):
    acrescimo = request.json['acrescimo']
    c.execute('UPDATE partidas SET acrescimo = ? WHERE id = ?', (acrescimo, partida_id,))
    c.execute('INSERT INTO eventos (partida_id, tipo, tempo) VALUES (?, ?, ?)', (partida_id, 'acrescimo', request.json['tempo'],))
    conn.commit()
    return jsonify({'mensagem': 'Acréscimo registrado com sucesso.'})

# Rota para adicionar substituicao
@app.route('/torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/substituicao', methods=['POST'])
def registrar_substituicao(torneio_id, partida_id):
    dados = request.get_json()
    jogador_entrada_id = dados['jogador_entrada_id']
    jogador_saida_id = dados['jogador_saida_id']
    tempo = dados['tempo']

    # Verifica se a partida e o torneio existem
    partida = c.execute('SELECT id FROM partidas WHERE id = ? AND torneio_id = ?', (partida_id, torneio_id)).fetchone()
    if not partida:
        return jsonify({'erro': 'Partida não encontrada'}), 404

    # Insere o evento na tabela eventos_partida
    c.execute('INSERT INTO eventos_partida (partida_id, tipo, jogador_entrada_id, jogador_saida_id, tempo) VALUES (?, ?, ?, ?, ?)',
              (partida_id, 'substituicao', jogador_entrada_id, jogador_saida_id, tempo))
    conn.commit()

    return jsonify({'mensagem': 'Substituição registrada com sucesso.'}), 200

# Rota para adicionar advertencia
@app.route('/torneios/<int:id_torneio>/partidas/<int:id_partida>/eventos/advertencia', methods=['POST'])
def add_advertencia(id_torneio, id_partida):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    jogador_id = request.json['jogador_id']
    minuto = request.json['minuto']
    tipo = request.json['tipo']

    c.execute('''INSERT INTO eventos_partida (partida_id, tipo, jogador_id, minuto)
                 VALUES (?, ?, ?, ?)''', (id_partida, tipo, jogador_id, minuto))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Advertência adicionada com sucesso.'}), 201

# Rota para adicionar fim da partida
@app.route('/torneios/<int:id_torneio>/partidas/<int:id_partida>/eventos/fim', methods=['POST'])
def add_fim(id_torneio, id_partida):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    gol_casa = request.json['gol_casa']
    gol_visitante = request.json['gol_visitante']
    fim = request.json['fim']

    c.execute('''UPDATE partidas SET gol_casa = ?, gol_visitante = ?, fim = ?
                 WHERE id = ?''', (gol_casa, gol_visitante, fim, id_partida))

    conn.commit()
    conn.close()

    return jsonify({'message': 'Fim da partida adicionado com sucesso.'}), 200

# --------------------------------------------- Configuração do Swagger -----------------------------------------------------------

# Configuração do Swagger
SWAGGER_URL = '/api/docs'
API_URL = '/api/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "API de Transferências"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Configuração do Swagger
@app.route('/api/spec')
def swagger_spec():
    swag = swagger(app)
    swag['info']['title'] = 'API de Transferências'
    swag['info']['description'] = 'API para gerenciamento de transferências de jogadores entre times'
    swag['info']['version'] = '1.0'
    swag['basePath'] = '/'
    
    swag['paths']['/time'] = {
    'post': {
        'summary': 'Criar um time',
        'description': 'Cria um novo time com o nome e localidade informados',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'description': 'Dados do time a ser criado',
                'required': True,
                'schema': {
                    '$ref': '#/definitions/Time'
                }
            }
        ],
        'responses': {
            '200': {
                'description': 'Time criado com sucesso',
                'schema': {
                    '$ref': '#/definitions/Time'
                }   
                }   
            }
        }
    }

    swag['paths']['/time/{id}'] = {
        'get': {
            'summary': 'Buscar um time',
            'description': 'Busca um time pelo seu ID',
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'description': 'ID do time a ser buscado',
                    'required': True,
                    'type': 'integer'
                }
            ],
            'responses': {
                '200': {
                    'description': 'Time encontrado com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Time'
                    }
                },
                '404': {
                    'description': 'Time não encontrado'
                }
            }
        },
        'put': {
            'summary': 'Atualizar um time',
            'description': 'Atualiza o nome e localidade de um time existente',
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'description': 'ID do time a ser atualizado',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Novos dados do time',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/Time'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Time atualizado com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Time'
                    }
                },
                '404': {
                    'description': 'Time não encontrado'
                }
            }
        }
    }
    
    swag['paths']['/jogador'] = {
        'post': {
            'summary': 'Criar um jogador',
            'description': 'Cria um novo jogador com o nome, data de nascimento, país e time informados',
            'parameters': [
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do jogador a ser criado',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/Jogador'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Jogador criado com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Jogador'
                    }
                }
            }
        }
    }
    
    # Descrição do endpoint /jogadores
    swag['paths']['/jogadores'] = {
        'get': {
            'summary': 'Listar jogadores',
            'description': 'Retorna uma lista com todos os jogadores cadastrados',
            'responses': {
                '200': {
                    'description': 'Lista de jogadores',
                    'schema': {
                        'type': 'array',
                        'items': {
                            '$ref': '#/definitions/Jogador'
                        }
                    }
                }
            }
        }
    }
    
    swag['paths']['/jogador/{id}'] = {
    'get': {
        'summary': 'Buscar um jogador',
        'description': 'Busca um jogador pelo seu ID',
        'parameters': [
            {
                'name': 'id',
                'in': 'path',
                'description': 'ID do jogador a ser buscado',
                'required': True,
                'type': 'int'
            }
        ],
            'responses': {
                        '200': {
                        'description': 'Jogador encontrado',
                        'content': {
                            'application/json': {
                                            'schema': {
                                                '$ref': '#/definitions/Jogador'
                                                    }
                                                }
                                    }
                                },
                                '404': {
                                    'description': 'Jogador não encontrado'
                                }
                        }
                }
    }
    
    # Descrição do endpoint /transferencias
    swag['paths']['/transferencias'] = {
        'post': {
            'summary': 'Criar transferência',
            'description': 'Cria uma nova transferência de um jogador de um time para outro',
            'parameters': [
                {
                    'name': 'transferencia',
                    'in': 'body',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/TransferenciaInput'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Transferência criada com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Transferencia'
                    }
                },
                '400': {
                    'description': 'Erro na requisição',
                    'schema': {
                        '$ref': '#/definitions/Erro'
                    }
                }
            }
        }
    }
    
    # Para o endpoint de criar transferência, temos:
    swag['paths']['/transferencia'] = {
        'post': {
            'summary': 'Criar uma transferência',
            'description': 'Cria uma transferência de um jogador de um time para outro',
            'parameters': [
                {
                    'name': 'jogador_id',
                    'in': 'body',
                    'description': 'ID do jogador a ser transferido',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'time_origem_id',
                    'in': 'body',
                    'description': 'ID do time de origem',
                    'required': True,
                    'type': 'integer'
                    },
                {
                    'name': 'time_destino_id',
                    'in': 'body',
                    'description': 'ID do time de destino',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'data',
                    'in': 'body',
                    'description': 'Data da transferência (formato: "YYYY-MM-DD")',
                    'required': True,
                    'type': 'string'
                },
                {
                    'name': 'valor',
                    'in': 'body',
                    'description': 'Valor da transferência',
                    'required': True,
                    'type': 'number'
                }
            ],
            'responses': {
                '201': {
                    'description': 'Transferência criada com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Transferencia'
                        }
                    },
                '404': {
                    'description': 'Jogador, time de origem ou time de destino não encontrado'
                    }
            }
        }
    }
    
    # Para o endpoint de buscar transferências de um jogador, temos: 
    
    swag['paths']['/jogador/{id}/transferencias'] = {
        'get': {
            'summary': 'Buscar as transferências de um jogador',
            'description': 'Retorna todas as transferências de um jogador',
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'description': 'ID do jogador',
                    'required': True,
                    'type': 'integer'
                }
                    ],
        'responses': {
            '200': {
                'description': 'Lista de transferências',
                'schema': {
                    'type': 'array',
                                'items': {
                                    '$ref': '#/definitions/Transferencia'
                                }
                            }
                    },
        '404': {
            'description': 'Jogador não encontrado'
                }
            }
        }
    }
    
    # Para o endpoint de listar todas as transferências, temos:
    swag['paths']['/transferencias'] = {
        'get': {
            'summary': 'Listar todas as transferências',
            'description': 'Retorna todas as transferências realizadas',
            'responses': {
                '200': {
                    'description': 'Lista de transferências',
                    'schema': {
                    'type': 'array',
                            'items': {
                                '$ref': '#/definitions/Transferencia'
                            }
                        }
                    }
                }
            }
        }
    
    # Para o endpoint de criar um torneio, temos:
    swag['paths']['/torneio'] = {
        'post': {
            'summary': 'Criar um torneio',
            'description': 'Cria um novo torneio com o nome e datas de início e fim informados',
            'parameters': [
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do torneio a ser criado',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/Torneio'
                        }
                    }
                ],
            'responses': {
                '200': {
                    'description': 'Torneio criado com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Torneio'
                        }
                    }
                }
            }
    }
    
    # Para o endpoint de buscar um torneio, temos:
    swag['paths']['/torneio/int:id'] = {
        'get': {
            'summary': 'Buscar um torneio',
            'description': 'Busca um torneio com o ID informado',
            'responses': {
                '200': {
                    'description': 'Torneio encontrado',
                    'schema': {
                        '$ref': '#/definitions/Torneio'
                    }
                },
                '404': {
                    'description': 'Torneio não encontrado'
                }
            }
        },
        'put': {
            'summary': 'Atualizar um torneio',
            'description': 'Atualiza as informações de um torneio com o ID informado',
            'parameters': [
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do torneio a ser atualizado',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/Torneio'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Torneio atualizado com sucesso',
                    'schema': {
                        '$ref': '#/definitions/Torneio'
                    }
                },
                '404': {
                    'description': 'Torneio não encontrado'
                }
            }
        }
    }
    
    # Para o endpoint de criar uma partida, temos:
    swag['paths']['/partida'] = {
        'post': {
        'summary': 'Criar uma partida',
        'description': 'Cria uma nova partida com as informações do torneio, times, data, local e resultado informados',
        'parameters': [
            {
                'name': 'body',
                'in': 'body',
                'description': 'Dados da partida a ser criada',
                'required': True,
                    'schema': {
                        '$ref': '#/definitions/Partida'
                    }
            }
        ],
        'responses': {
            '201': {
                'description': 'Partida criada com sucesso',
                'schema': {
                    '$ref': '#/definitions/Partida'
                }
            },
            '404': {
                'description': 'Torneio, time da casa ou time visitante não encontrado'
                }
            }
        }
    }
    
    # Para o endpoint de buscar as partidas de um torneio, temos:
    swag['paths']['/torneio/int:id/partidas'] = {
        'get': {
            'summary': 'Buscar as partidas de um torneio',
            'description': 'Busca as partidas de um torneio com o ID informado',
            'responses': {
                '200': {
                    'description': 'Partidas encontradas',
                    'schema': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/Partida'
                        }
                    }
                },
                '404': {
                    'description': 'Torneio não encontrado'
                    }
            }
        }
    }
    
    # Para o endpoint para registrar o início de uma partida de um torneio, temos:
    swag['paths']['/torneios/{torneio_id}/partidas/{partida_id}/eventos/inicio'] = {
        'post': {
            'summary': 'Registrar início da partida',
            'description': 'Registra o momento em que a partida de um torneio começou',
            'parameters': [
                {
                    'name': 'torneio_id',
                    'in': 'path',
                    'description': 'ID do torneio em que a partida está acontecendo',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'partida_id',
                    'in': 'path',
                    'description': 'ID da partida a ter o início registrado',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'tempo',
                    'in': 'body',
                    'description': 'Tempo em que a partida iniciou',
                    'required': True,
                    'type': 'string'
                }
            ],
            'responses': {
                '200': {
                    'description': 'Início da partida registrado com sucesso',
                    'schema': {
                        'mensagem': 'string'
                    }
                }
            }
        }
    }
    
    # Definição do schema para um evento de gol
    schema_gol = {
        'type': 'object',
        'properties': {
            'tempo': {'type': 'string', 'description': 'Tempo em que ocorreu o gol no formato hh:mm:ss'},
            'time': {'type': 'string', 'description': 'Time que marcou o gol ("casa" ou "visitante")'},
            'gol': {'type': 'integer', 'description': 'Número do jogador que marcou o gol'}
        },
        'required': ['tempo', 'time', 'gol']
    }
    
    swag['paths']['/torneios/{torneio_id}/partidas/{partida_id}/eventos/gol'] = {
        'post': {
            'summary': 'Registrar um gol',
            'description': 'Registra um gol em uma partida de futebol',
            'parameters': [
                {
                    'name': 'torneio_id',
                    'in': 'path',
                    'description': 'ID do torneio',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'partida_id',
                    'in': 'path',
                    'description': 'ID da partida',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do gol a ser registrado',
                    'required': True,
                    'schema': schema_gol
                }
            ],
            'responses': {
                '200': {
                    'description': 'Gol registrado com sucesso',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'mensagem': {'type': 'string', 'description': 'Mensagem de confirmação'}
                        }
                    }
                }
            }
        }
    }
    
    # Documentação do endpoint de registro de intervalo
    swag['paths']['/torneios/{torneio_id}/partidas/{partida_id}/eventos/intervalo'] = {
        'post': {
            'summary': 'Registrar intervalo na partida',
            'description': 'Registra o intervalo de tempo na partida',
            'parameters': [
                {
                    'name': 'torneio_id',
                    'in': 'path',
                    'description': 'ID do torneio',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'partida_id',
                    'in': 'path',
                    'description': 'ID da partida',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do intervalo a ser registrado',
                    'required': True,
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'tempo': {
                                'type': 'string',
                                'description': 'Tempo de duração do intervalo no formato HH:MM:SS'
                            }
                        }
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Intervalo registrado com sucesso',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'mensagem': {
                                'type': 'string',
                                'description': 'Mensagem de sucesso'
                            }
                        }
                    }
                },
                '400': {
                    'description': 'Requisição inválida',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'erro': {
                                'type': 'string',
                                'description': 'Descrição do erro'
                            }
                        }
                    }
                },
                '404': {
                    'description': 'Partida não encontrada',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'erro': {
                                'type': 'string',
                                'description': 'Descrição do erro'
                            }
                        }
                    }
                },
                '500': {
                    'description': 'Erro interno do servidor',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'erro': {
                                'type': 'string',
                                'description': 'Descrição do erro'
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Esta documentação especifica que uma solicitação POST para o endpoint /torneios/<int:torneio_id>/partidas/<int:partida_id>/eventos/acrescimo deve incluir uma carga útil JSON com o acrescimo (em minutos) e o tempo (no formato de " 45+2" por exemplo). A resposta a uma solicitação bem-sucedida é uma carga útil JSON contendo um campo de mensagem com uma mensagem de sucesso.
    swag['paths']['/torneios/{torneio_id}/partidas/{partida_id}/eventos/acrescimo'] = {
        'post': {
            'summary': 'Registrar acréscimo de tempo em uma partida',
            'description': 'Registra o acréscimo de tempo em uma partida de futebol',
            'parameters': [
                {
                    'name': 'torneio_id',
                    'in': 'path',
                    'description': 'ID do torneio',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'partida_id',
                    'in': 'path',
                    'description': 'ID da partida',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do acréscimo de tempo a serem registrados',
                    'required': True,
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'acrescimo': {
                                'type': 'string',
                                'description': 'Acréscimo de tempo em minutos'
                            },
                            'tempo': {
                                'type': 'string',
                                'description': 'Tempo em que ocorreu o acréscimo (ex: "45+2")'
                            }
                        }
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Acréscimo registrado com sucesso.',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'mensagem': {
                                'type': 'string',
                                'description': 'Mensagem de confirmação'
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Definição de tipos
    swag['definitions']['Evento'] = {
        'type': 'object',
        'properties': {
            'jogador_id': {
                'type': 'integer',
                'description': 'ID do jogador que recebeu a advertência'
            },
            'minuto': {
                'type': 'integer',
                'description': 'Minuto da partida em que ocorreu o evento'
            },
            'tipo': {
                'type': 'string',
                'description': 'Tipo de evento (advertência, expulsão, gol, etc.)'
            }
        }
    }

    # # Documentação do endpoint de criação de evento de advertência
    swag['paths']['/torneios/{id_torneio}/partidas/{id_partida}/eventos/advertencia'] = {
        'post': {
            'summary': 'Adicionar uma advertência a um jogador',
            'description': 'Registra um evento de advertência na partida para o jogador especificado',
            'parameters': [
                {
                    'name': 'id_torneio',
                    'in': 'path',
                    'description': 'ID do torneio',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'id_partida',
                    'in': 'path',
                    'description': 'ID da partida',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'Evento',
                    'in': 'body',
                    'description': 'Informações do evento',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/Evento'
                    }
                }
            ],
            'responses': {
                '201': {
                    'description': 'Evento registrado com sucesso'
                },
                '404': {
                    'description': 'Partida não encontrada'
                }
            }
        }
    }   
    
    # o endpoint add_fim
    swag['paths']['/torneios/{id_torneio}/partidas/{id_partida}/eventos/fim'] = {
        'post': {
            'summary': 'Adicionar o fim da partida',
            'description': 'Adiciona o resultado final da partida, atualizando o número de gols de cada equipe e o tempo final do jogo.',
            'parameters': [
                {
                    'name': 'id_torneio',
                    'in': 'path',
                    'description': 'ID do torneio a que a partida pertence',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'id_partida',
                    'in': 'path',
                    'description': 'ID da partida a ser atualizada',
                    'required': True,
                    'type': 'integer'
                },
                {
                    'name': 'body',
                    'in': 'body',
                    'description': 'Dados do resultado final da partida',
                    'required': True,
                    'schema': {
                        '$ref': '#/definitions/FimPartida'
                    }
                }
            ],
            'responses': {
                '200': {
                    'description': 'Fim da partida adicionado com sucesso',
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'message': {
                                'type': 'string',
                                'description': 'Mensagem indicando que o fim da partida foi adicionado com sucesso'
                            }
                        }
                    }
                },
                '404': {
                    'description': 'Partida ou torneio não encontrados'
                },
                '500': {
                    'description': 'Erro interno do servidor'
                }
            }
        }
    }
    
    # Documentação do endpoint de registro de substituicao
    swag['paths']['/torneios/{torneio_id}/partidas/{partida_id}/eventos/substituicao'] = {
        'post': {
                'summary': 'Registrar substituição',
                'description': 'Registra uma substituição realizada durante uma partida do torneio',
                'consumes': ['application/json'],
                'produces': ['application/json'],
                'parameters': [
                    {
                        'name': 'torneio_id',
                        'in': 'path',
                        'description': 'ID do torneio',
                        'required': True,
                        'type': 'integer'
                    },
                    {
                        'name': 'partida_id',
                        'in': 'path',
                        'description': 'ID da partida',
                        'required': True,
                        'type': 'integer'
                    },
                    {
                        'name': 'body',
                        'in': 'body',
                        'description': 'Dados da substituição',
                        'required': True,
                        'schema': {
                            '$ref': '#/definitions/Substituicao'
                        }
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Substituição registrada com sucesso.',
                        'schema': {
                            '$ref': '#/definitions/Mensagem'
                        }
                    },
                    '404': {
                        'description': 'Partida não encontrada',
                        'schema': {
                            '$ref': '#/definitions/Erro'
                        }
                    }
                }
            }            
        }

    
    # ---------------------------------------- Definição dos modelos ----------------------------------------------------
    
    # Definição do modelo Jogador
    swag['definitions']['Jogador'] = {
        'type': 'object',
        'properties': {
            'nome': {
                'type': 'string'
            },
            'data_nascimento': {
                'type': 'string'
            },
            'pais': {
                'type': 'string'
            },
            'time': {
                'type': 'string'
            }
        }
    }

    # Definição do modelo Time
    swag['definitions']['Time'] = {
        'type': 'object',
        'properties': {
            'nome': {
                'type': 'string'
            },
            'localidade': {
                'type': 'string'
            }
        }
    }

    # Definição do modelo Transferencia
    swag['definitions']['Transferencia'] = {
        'type': 'object',
        'properties': {
            'jogador': {
                '$ref': '#/definitions/Jogador'
            },
            'time_origem': {
                '$ref': '#/definitions/Time'
            },
            'time_destino': {
                '$ref': '#/definitions/Time'
            },
            'data': {
                'type': 'string'
            },
            'valor': {
                'type': 'number'
            }
        }
    }

    # Definição do modelo de entrada para Transferencia
    swag['definitions']['TransferenciaInput'] = {
        'type': 'object',
        'required': ['jogador', 'time_origem', 'time_destino', 'data', 'valor'],
        'properties': {
            'jogador': {
                'type': 'string'
            },
            'time_origem': {
                'type': 'string'
            },
            'time_destino': {
                'type': 'string'
            },
            'data': {
                'type': 'string'
            },
            'valor': {
                'type': 'number'
            }
        }
    }
    
     # Definição do modelo de entrada para FimPartida
    swag['definitions']['FimPartida'] = {
        'type': 'object',
        'properties': {
            'gol_casa': {
                'type': 'integer',
                'description': 'Número de gols marcados pela equipe da casa'
            },
            'gol_visitante': {
                'type': 'integer',
                'description': 'Número de gols marcados pela equipe visitante'
            },
            'fim': {
                'type': 'string',
                'description': 'Tempo final da partida no formato "hh:mm:ss"'
            }
        },
        'required': ['gol_casa', 'gol_visitante', 'fim']
    }
    
    # Definição do modelo de entrada para Substituicao
    swag['definitions']['Substituicao'] = {
        'type': 'object',
                'properties': {
                    'jogador_entrada_id': {
                        'type': 'integer',
                        'description': 'ID do jogador que entrou na partida'
                    },
                    'jogador_saida_id': {
                        'type': 'integer',
                        'description': 'ID do jogador que saiu da partida'
                    },
                    'tempo': {
                        'type': 'string',
                        'description': 'Tempo em que a substituição ocorreu'
                    }
                },
                'required': ['jogador_entrada_id', 'jogador_saida_id', 'tempo']
    } 

    # Definição do modelo de erro
    swag['definitions']['Erro'] = {
        'type': 'object',
        'properties': {
            'mensagem': {
                'type': 'string'
            }
        }
    }

    return jsonify(swag)

# Executa a aplicação Flask
if __name__ == "__main__":
    app.run(debug=True)

# Para testar a sua aplicação, primeiro é necessário executá-la. 
# Para isso, basta executar o seguinte comando no terminal dentro do diretório 
# em que o arquivo da sua aplicação se encontra:
    
# python nome_do_arquivo.py

# Substitua nome_do_arquivo pelo nome do arquivo da sua aplicação.
# Depois de executar a sua aplicação, abra o navegador e acesse o seguinte endereço:
    
# http://localhost:5000/swagger/

# http://localhost:5000/api/docs/

# O número 5000 pode variar dependendo da porta em que a sua aplicação está sendo executada.

# Essa rota irá exibir a interface Swagger, que você pode usar para testar os endpoints da sua API. Todos os endpoints definidos no seu arquivo nome_do_arquivo.py devem aparecer na interface Swagger, juntamente com os campos necessários para preencher as requisições.

# Basta preencher os campos e clicar em "Try it out!" para enviar a requisição. O resultado da requisição será exibido abaixo, juntamente com o status da resposta.