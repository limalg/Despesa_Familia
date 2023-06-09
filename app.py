import requests
from flask import Flask, render_template, request, redirect
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

app = Flask(__name__)

# Variável Global
categorias = [
    ' ',
    'Alimentação',
    'Itens Comuns',
    'Viagem',
    'Compras Parceladas',
    'Fim de Semana',
    'Luz',
    'Condominio',
    'Gas',
    'Aluguel',
    'Investimento Foz',
    'Mercado',
    'Internet',
    'Transporte',
    'Seguro contra incêndio',
    'Pet',
    'Facily',
    'Faxina'
]
"""
@app.before_first_request
def create_table():
    db.create_all()
"""

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        return render_template('createpage.html', categorias=categorias)

    if request.method == 'POST':
        
        usuario = request.form['usuario']
        pagamento = request.form['pagamento']
        data = request.form['data']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        valor = request.form['valor']
        parcela = request.form['parcela']
        tipo_despesa = request.form['tipo_despesa']
        

        if int(parcela) > 1:
            data = datetime.strptime(data, '%Y-%m-%d')
            parcelas = int(parcela) + 1
            for num in range(1, parcelas, 1):
                nova_data = data + relativedelta(months=num)
                nova_data = nova_data.strftime('%Y-%m-%d')
                despesa = {
                    'data': nova_data,
                    'descricao': descricao,
                    'categoria': categoria,
                    'valor': valor,
                    'parcela': num,
                    'usuario': usuario,
                    'pagamento': pagamento,
                    'id':True,
                    'tipo_despesa':tipo_despesa
                }
                create_record(despesa)
        else:
            despesa = {
                'data': data,
                'descricao': descricao,
                'categoria': categoria,
                'valor': valor,
                'parcela': parcela,
                'usuario': usuario,
                'pagamento': pagamento,
                'id':True,
                'tipo_despesa':tipo_despesa
            }
            create_record(despesa)
        return redirect('/')


@app.route('/')
def presentation():
    despesas = retrieve_records()
    return render_template('presentation.html', despesas=despesas)

@app.route('/list')
def retrieve_list():
    despesas = retrieve_records()
    return render_template('datalist.html', despesas=despesas)


@app.route('/<string:id>/edit', methods=['GET', 'POST'])
def update(id):
    despesa = retrieve_record(id)

    if request.method == 'POST':
        if despesa:
            despesa['usuario'] = request.form['usuario']
            despesa['pagamento'] = request.form['pagamento']
            despesa['data'] = request.form['data']
            despesa['descricao'] = request.form['descricao']
            despesa['categoria'] = request.form['categoria']
            despesa['valor'] = request.form['valor']
            despesa['parcela'] = request.form['parcela']
            despesa['tipo_despesa'] = request.form['tipo_despesa']
            update_record(id, despesa)
            return redirect('/')
        return f"A despesa com o ID {id} não existe."

    return render_template('update.html', despesa=despesa, categorias=categorias)


@app.route('/<string:id>/delete', methods=['GET', 'POST'])
def delete(id):
    despesa = retrieve_record(id)

    if request.method == 'POST':
        if despesa:
            delete_record(id)
            return redirect('/')
        abort(404)

    return render_template('delete.html')

@app.route('/dashboard')
def dashboard():
    #despesas = retrieve_records()
    despesas = records_month_atual()
    return render_template('dashboard.html', despesas=despesas)

@app.route('/dashboard1')
def dashboard1():
    despesas = retrieve_records_month()
    #item_selecionado = request.args.get('link_anomes')
    #item_selecionado = request.form['filtroAnoMes']
    #print(item_selecionado)
    return render_template('dashboard1.html', despesas=despesas)


######################################################
# Funções auxiliares
######################################################
link = 'https://casa-9085b-default-rtdb.firebaseio.com/'

# Função para criar um novo registro
def create_record(data):
    response = requests.post(f'{link}despesa.json', json=data)
    if response.status_code == 200:
        record_id = response.json()['name']
        update_record(record_id, {'id': record_id})
        print('Novo registro criado com sucesso.')
    else:
        print('Erro ao criar registro:', response.text)


# Função para recuperar todos os registros
def retrieve_records():
    response = requests.get(f'{link}despesa.json')
    if response.status_code == 200:
        data = response.json()
        return list(data.values()) if data else []
    else:
        print('Erro ao recuperar registros:', response.text)
        return []


# Função para recuperar um registro específico
def retrieve_record(id):
    response = requests.get(f'{link}despesa/{id}.json')
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Erro ao recuperar registro com o ID {id}:', response.text)
        return None


# Função para atualizar um registro
def update_record(id, data):
    response = requests.patch(f'{link}despesa/{id}.json', json=data)
    #response = requests.put(f'{link}despesa/{id}.json', json=data)
    if response.status_code == 200:
        print(f'Registro com o ID {id} atualizado com sucesso.')
    else:
        print(f'Erro ao atualizar registro com o ID {id}:', response.text)


# Função para excluir um registro
def delete_record(id):
    response = requests.delete(f'{link}despesa/{id}.json')
    if response.status_code == 200:
        print(f'Registro com o ID {id} excluído com sucesso.')
    else:
        print(f'Erro ao excluir registro com o ID {id}:', response.text)

# Função para recuperar os registros do Mês Atual
def retrieve_records_month():
    response = requests.get(f'{link}despesa.json')
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df = df.transpose()
        df['data'] = pd.to_datetime(df['data'])
        df['anomes'] = df['data'].dt.strftime('%Y%m' )
        df['ano'] = df['data'].dt.strftime('%Y' )
        df['mes'] = df['data'].dt.strftime('%m' )
        df['dia'] = df['data'].dt.strftime('%d' )
        df['valor'] = df['valor'].astype(float)
        df['dia'] = df['dia'].astype('Int64')
        #df = df.loc[df['anomes'] == id_anomes]
        # Agrupar pelas colunas 'hoje' e 'nome' e redefinir o índice
        #df = df.groupby(['anomes', 'categoria']).agg({'valor':sum}).reset_index()
        df = df[['anomes','ano','mes','dia','data','valor','categoria','descricao','pagamento','parcela' ,'tipo_despesa', 'usuario', 'id']]
        df = df.reset_index(drop=True)
        #print(df)
        return df
    else:
        print('Erro ao recuperar registros:', response.text)
        return []

# Função para recuperar os registros do Mês Atual
def records_month_atual():
    response = requests.get(f'{link}despesa.json')
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        df = df.transpose()
        df['data'] = pd.to_datetime(df['data'])
        df['anomes'] = df['data'].dt.strftime('%Y%m' )
        df['mes'] = df['data'].dt.strftime('%B')
        df['valor'] = df['valor'].astype(float)
        current_month = pd.to_datetime('today').strftime('%Y%m')
        df = df.loc[df['anomes'] == current_month]
        # Agrupar pelas colunas 'hoje' e 'nome' e redefinir o índice
        df = df.groupby(['categoria','mes','tipo_despesa','usuario','anomes']).agg({'valor':sum}).reset_index()
        return df
    else:
        print('Erro ao recuperar registros:', response.text)
        return []

if __name__ == '__main__':
    #app.run(debug=True)
    app.run()
