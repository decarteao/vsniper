
from concurrent.futures import ThreadPoolExecutor
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, jsonify, render_template, redirect, url_for, request, flash
from sqlalchemy import desc


from datetime import datetime
from controllers.monitor_prices import MonitorPrices
from models.database import db, User, Exchanges, Monitor


# utisls
mp = MonitorPrices()

# web
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Nos.Tiv3m0s#Ond3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///models/vsniper.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

USER, PASSWD = 'victor', '#3He.Victor12@'

# confing context
with app.app_context():
    db.init_app(app=app)
    db.create_all(app=app)

    user = User.query.filter_by(user=USER, password=PASSWD).first()
    if not user:
        # add user admin
        db.session.add(User(user=USER, password=PASSWD))

        # add exchanges
        for nome in ['Binance', 'BingX', 'Bitget', 'Bitrue', 'Mercado Bitcoin', 'MEXC', 'OKX']:
            db.session.add(Exchanges(nome=nome))
            
        db.session.commit()
    
    # iniciar o que ja esta no db

    for row in Monitor.query.all():
        if row.par not in getattr(mp, row.exchange1 + '_ws').pares:
            getattr(mp, row.exchange1 + '_ws').moedas_order_book = {}
            getattr(mp, row.exchange1 + '_ws').pares.append(row.par)
            getattr(mp, row.exchange1 + '_ws').stop()
            getattr(mp, row.exchange1 + '_ws').start()
        if row.par not in getattr(mp, row.exchange2 + '_ws').pares:
            getattr(mp, row.exchange2 + '_ws').moedas_order_book = {}
            getattr(mp, row.exchange2 + '_ws').pares.append(row.par)
            getattr(mp, row.exchange2 + '_ws').stop()
            getattr(mp, row.exchange2 + '_ws').start()
    


# login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Define a rota para login

# Função de carregamento de usuário
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Criando rotas

## Pagina Inicial do Client
@app.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        isOn = request.form.get('isOn', -1)
        if isOn != -1:
            # ligar ou desligar o bot
            current_user.isBotOn = isOn
            db.session.commit()
            return '-'
    return render_template('user/index.html', isOn=current_user.isBotOn == 1)

@app.route('/monitor', methods=['GET','POST'])
@login_required
def monitor():
    if request.method == 'POST':
        par = request.form.get('par', '').upper()
        spread = float(request.form.get('spread', 0.01)) # %

        if not par or '-' not in par:
            flash('Escolha um par válido')
        else:
            # buscar as exchanges que possuem esses pares
            lista = mp.get_exchanges_with_par(par)
            # validar exchanges
            if len(lista) == 0:
                flash('Nenhuma exchange possu: ' + par)
            elif len(lista) == 1:
                flash('Apenas uma exchange possui este par: ' + par)
            else:
                # entre-lacar
                combinancoes = []
                for exc in lista:
                    for exc2 in lista:
                        if exc != exc2 and [exc, exc2] not in combinancoes and [exc2, exc] not in combinancoes:
                            q = Monitor.query.filter_by(exchange1=exc, exchange2=exc2, par=par).first()
                            q2 = Monitor.query.filter_by(exchange1=exc2, exchange2=exc, par=par).first()
                            if not q and not q2:
                                if not getattr(mp, exc + '_ws').isOn:
                                    getattr(mp, exc + '_ws').pares.append(par)
                                    getattr(mp, exc + '_ws').start()
                                elif par not in getattr(mp, exc + '_ws').pares:
                                    getattr(mp, exc + '_ws').moedas_order_book = {}
                                    getattr(mp, exc + '_ws').pares.append(par)
                                    getattr(mp, exc + '_ws').stop()
                                    getattr(mp, exc + '_ws').start()

                                if not getattr(mp, exc2 + '_ws').isOn:
                                    getattr(mp, exc2 + '_ws').pares.append(par)
                                    getattr(mp, exc2 + '_ws').start()
                                elif par not in getattr(mp, exc2 + '_ws').pares:
                                    getattr(mp, exc2 + '_ws').moedas_order_book = {}
                                    getattr(mp, exc2 + '_ws').pares.append(par)
                                    getattr(mp, exc2 + '_ws').stop()
                                    getattr(mp, exc2 + '_ws').start()

                                combinancoes.append([exc, exc2])

                for exch1, exch2 in combinancoes:
                    # opah, salvar no monitor
                    m = Monitor(exchange1=exch1, exchange2=exch2, par=par, spread=spread, created_at=datetime.utcnow())
                    db.session.add(m)
                db.session.commit()
    
        return redirect('/monitor')
    elif request.args.get('del'):
        _id = int(request.args.get('del'))
        try:
            m = Monitor.query.get(_id)

            exchanges_usando = Monitor.query.filter_by(par=m.par).all()
            if len(exchanges_usando) == 1:
                if m.par in getattr(mp, m.exchange1 + '_ws').pares:
                    del getattr(mp, m.exchange1 + '_ws').pares[getattr(mp, m.exchange1 + '_ws').pares.index(m.par)]
                    getattr(mp, m.exchange1 + '_ws').moedas_order_book = {}
                    getattr(mp, m.exchange1 + '_ws').stop()
                    getattr(mp, m.exchange1 + '_ws').start()
                if m.par in getattr(mp, m.exchange2 + '_ws').pares:
                    del getattr(mp, m.exchange2 + '_ws').pares[getattr(mp, m.exchange2 + '_ws').pares.index(m.par)]
                    getattr(mp, m.exchange2 + '_ws').moedas_order_book = {}
                    getattr(mp, m.exchange2 + '_ws').stop()
                    getattr(mp, m.exchange2 + '_ws').start()

            db.session.delete(m)
            db.session.commit()
        except SystemError:
            pass
        return redirect('/monitor')

    exchanges = []
    for exchange in Exchanges.query.all():
        exchanges.append(exchange.nome)

    monitores = Monitor.query.order_by(desc(Monitor.id)).all()
    return render_template('user/monitor.html', exchanges=exchanges, monitores=monitores, row_monitores=len(monitores))

@app.route('/configs', methods=['GET','POST'])
@login_required
def configs():
    if request.method == 'POST':
        for exchange in Exchanges.query.all():
            if exchange.nome == 'Binance':
                exchange.api_key = request.form.get('api_token_binance', '')
                exchange.api_secret = request.form.get('api_secret_binance', '')
            elif exchange.nome == 'BingX':
                exchange.api_key = request.form.get('api_token_bingx', '')
                exchange.api_secret = request.form.get('api_secret_bingx', '')
            elif exchange.nome == 'Bitget':
                exchange.api_key = request.form.get('api_token_bitget', '')
                exchange.api_secret = request.form.get('api_secret_bitget', '')
            elif exchange.nome == 'Bitrue':
                exchange.api_key = request.form.get('api_token_bitrue', '')
                exchange.api_secret = request.form.get('api_secret_bitrue', '')
            elif exchange.nome == 'Mercado Bitcoin':
                exchange.api_key = request.form.get('api_token_mb', '')
                exchange.api_secret = request.form.get('api_secret_mb', '')
            elif exchange.nome == 'MEXC':
                exchange.api_key = request.form.get('api_token_mexc', '')
                exchange.api_secret = request.form.get('api_secret_mexc', '')
            elif exchange.nome == 'OKX':
                exchange.api_key = request.form.get('api_token_okx', '')
                exchange.api_secret = request.form.get('api_secret_okx', '')
        db.session.commit()
        return redirect('/configs')

    datas = {}
    for exchange in Exchanges.query.all():
        datas[exchange.nome] = [exchange.api_key, exchange.api_secret]

    return render_template('user/configs.html', datas=datas)

@app.route('/login', methods=['GET','POST'])
def login():
    logout_user()

    if request.method == 'POST':
        user = request.form.get('user', '')
        passwd = request.form.get('password', '')

        if not user or not passwd:
            flash('Preencha todos os campos')
            return redirect('/login')
        
        # continuar o processo de login
        user_obj = User.query.filter_by(user=user, password=passwd).first()
        if not user_obj:
            flash('Credenciais incorrectas')
            return redirect('/login')

        # continuar com o processo de login
        login_user(user_obj, remember=True)
        return redirect('/')
    
    return render_template('index.html')

@app.route('/logout')
def sair():
    logout_user()
    return redirect('/login')

## OUTRAS ROTAS DO PAINEL
@app.route('/api', methods=['GET', 'POST'])
def api():
    if request.method == 'POST':
        method = request.form.get('method', 'pares')
        return jsonify({"status":"ok"})
    
    if request.args.get('exchange1') and request.args.get('exchange2'):
        exch1 = request.args.get('exchange1')
        exch2 = request.args.get('exchange2')

        try:
            return jsonify(mp.buscar_pares_iguais(exch1, exch2))
        except:
            return jsonify([])
@app.route('/api/pares', methods=['GET', 'POST'])
def api_pares():
    try:
        return jsonify(mp.pares)
    except:
        return jsonify([])
@app.route('/api/oportunity', methods=['GET', 'POST'])
def api_oportunidades():
    try:
        pares = []
        monitores = []
        for row in Monitor.query.all():
            monitores.append([row.id, row.exchange1, row.exchange2, row.par, row.spread])
        
        # buscar os precos
        with ThreadPoolExecutor(10) as tpe:
            results = tpe.map(mp.get_oportunity, monitores)
        
        for result in results:
            if result:
                pares.append(result)

        return jsonify(pares)
    except SystemError:
        return jsonify([])


# iniciar servidor
if __name__ == '__main__':
    app.run('0.0.0.0', port=80, debug=False)

