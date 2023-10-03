from flask import Flask, render_template, request, redirect,session,url_for
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import pyrebase
from functools import wraps
import os
import json

app = Flask(__name__)

#secret key for the session
app.secret_key = os.urandom(24)

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
    'Faxina',
    'Ticket Alimentação',
    'Ticket Carro',
    'Ticket Refeição'

]


# Carregue as configurações do Firebase do arquivo JSON local
with open('firebase_config.json', 'r') as config_file:
    config = json.load(config_file)

# Configurações do Firebase
firebase_config = {
    "apiKey": config["apiKey"],
    "authDomain": config["authDomain"],
    "databaseURL": config["databaseURL"],
    "projectId": config["projectId"],
    "storageBucket": config["storageBucket"],
    "messagingSenderId": config["messagingSenderId"],
    "appId": config["appId"]
}

# Inicialize o Firebase com as configurações carregadas
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()

#decorator to protect routes
def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #check for the variable that pyrebase creates
        if not auth.current_user != None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            #set the session
            user_id = user['idToken']
            user_email = email
            session['usr'] = user_id
            session["email"] = user_email
            return redirect("/")
        except Exception as e:
            print(e)
            return render_template('login.html', message='Credenciais inválidas')

    return render_template('login.html')

#logout route
@app.route("/logout")
def logout():
    #remove the token setting the user to None
    auth.current_user = None
    session.clear()
    return redirect("/")

@app.route('/create', methods=['GET', 'POST'])
@isAuthenticated
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
                    'id': True,
                    'tipo_despesa': tipo_despesa
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
                'id': True,
                'tipo_despesa': tipo_despesa
            }
            create_record(despesa)
        return redirect('/')


@app.route('/')
@isAuthenticated
def presentation():
    despesas = retrieve_records_month()
    return render_template('presentation.html', despesas=despesas)


@app.route('/list')
@isAuthenticated
def retrieve_list():
    despesas = retrieve_records()
    return render_template('datalist.html', despesas=despesas)


@app.route('/<string:id>/edit', methods=['GET', 'POST'])
@isAuthenticated
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
@isAuthenticated
def delete(id):
    despesa = retrieve_record(id)

    if request.method == 'POST':
        if despesa:
            delete_record(id)
            return redirect('/')
        abort(404)

    return render_template('delete.html')


@app.route('/dashboard')
@isAuthenticated
def dashboard():
    #despesas = retrieve_records_month() 
    despesas = records_month_atual()
        # Adicione uma nova coluna 'Despesa Fixa' com base nas categorias especificadas
    categorias_despesa_fixa = ['Alimentação','Gas','Internet', 'Aluguel', 'Condomínio', 'Faxina', 'Investimento Foz', 'Luz', 'Seguro contra incêndio']
    despesas['despesa_fixa'] = despesas['categoria'].apply(lambda x: 'Sim' if x in categorias_despesa_fixa else 'Não')
    despesas['data'] = despesas['data'].dt.strftime('%Y-%m-%d 15:00')
    return render_template('dashboard.html', despesas=despesas)


######################################################
# Funções auxiliares
######################################################


# Função para criar um novo registro
def create_record(data):
    response = db.child("despesa").push(data,token=session['usr'])
    record_id = response['name']
    update_record(record_id, {'id': record_id})
    print('Novo registro criado com sucesso.')


# Função para recuperar todos os registros
def retrieve_records():
    response = db.child("despesa").get(token=session['usr'])
    if response.val().keys():
        return list(response.val().values())
    else:
        print('Erro ao recuperar registros.')
        return []


# Função para recuperar um registro específico
def retrieve_record(id):
    response = db.child("despesa").child(id).get(token=session['usr'])
    if response.val():
        return response.val()
    else:
        print(f'Erro ao recuperar registro com o ID {id}.')
        return None


# Função para atualizar um registro
def update_record(id, data):
    db.child("despesa").child(id).update(data,token=session['usr'])
    print(f'Registro com o ID {id} atualizado com sucesso.')


# Função para excluir um registro
def delete_record(id):
    db.child("despesa").child(id).remove(token=session['usr'])
    print(f'Registro com o ID {id} excluído com sucesso.')


# Função para recuperar os registros do Mês Atual
def retrieve_records_month():
    response = db.child("despesa").get(token=session['usr'])
    if response.val():
        data = response.val()
        df = pd.DataFrame(data)
        df = df.transpose()
        df['data'] = pd.to_datetime(df['data'])
        df['ano'] = df['data'].dt.strftime('%Y')
        df['mes'] = df['data'].dt.strftime('%m')
        df['dia'] = df['data'].dt.strftime('%d')
        df['anomes'] = df['data'].dt.strftime('%Y%m')
        df['valor'] = df['valor'].astype(float)

        grouped_columns = ['categoria', 'anomes', 'tipo_despesa', 'dia']
        df_grouped = df.groupby(grouped_columns, as_index=False).agg({
            'data': 'first',
            'valor': 'sum',
            'ano': 'first',
            'mes': 'first'
        })

        # Ordenar o DataFrame pelos dias do maior para o menor
        df_grouped['dia'] = df_grouped['dia'].astype(int)  # Convert para int para garantir a ordem correta
        df_grouped = df_grouped.sort_values(by=['dia'], ascending=False)

        df_grouped = df_grouped[['categoria', 'anomes', 'tipo_despesa', 'dia', 'data', 'valor', 'ano', 'mes']]

        df_grouped = df_grouped.reset_index(drop=True)
        #print(df_grouped)
        return df_grouped
    else:
        print('Erro ao recuperar registros.')
        return []




# Função para recuperar os registros do Mês Atual (versão do autor)
def records_month_atual():
    response = db.child("despesa").get(token=session['usr'])
    if response.val():
        data = response.val()
        df = pd.DataFrame(data)
        df = df.transpose()
        df['data'] = pd.to_datetime(df['data'])
        df['anomes'] = df['data'].dt.strftime('%Y%m' )
        df['ano'] = df['data'].dt.strftime('%Y')
        df['mes'] = df['data'].dt.strftime('%m')
        df['dia'] = df['data'].dt.strftime('%d')
        df['valor'] = df['valor'].astype(float)
        #df['dia'] = df['dia'].astype('int')
        #current_month = pd.to_datetime('today').strftime('%Y%m')
        #df = df.loc[df['anomes'] == current_month]
        #df = df.reset_index(drop=True)
        #print(df)
        return df
    else:
        print('Erro ao recuperar registros.')
        return []


if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0')
    

