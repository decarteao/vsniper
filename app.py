
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask import Flask, jsonify, render_template, redirect, url_for, request, flash
from sqlalchemy import desc


from datetime import datetime
from models.database import db, User, Exchanges, Monitor



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
        exch1 = request.form.get('exchange1', '')
        exch2 = request.form.get('exchange2', '')
        par = request.form.get('par', '')
        oportunidade = float(request.form.get('oportunidade', 0.01)) # %

        if not exch1 or not exch2:
            flash('Escolha as exchanges')
        elif exch1 == exch2:
            flash('As exchanges não podem ser as mesmas')
        elif not par:
            flash('Escolha um par válido')
        else:
            # opah, salvar no monitor
            m = Monitor(exchange1=exch1, exchange2=exch2, par=par, oportunidade=oportunidade, created_at=datetime.utcnow())
            db.session.add(m)
            db.session.commit()
    
        return redirect('/monitor')
    elif request.args.get('del'):
        _id = int(request.args.get('del'))
        try:
            db.session.delete(Monitor.query.get(_id))
            db.session.commit()
        except:
            pass
        return redirect('/monitor')

    exchanges = []
    for exchange in Exchanges.query.all():
        exchanges.append(exchange.nome)

    return render_template('user/monitor.html', exchanges=exchanges, monitores=Monitor.query.order_by(desc(Monitor.id)).all())

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

# iniciar servidor
if __name__ == '__main__':
    app.run('0.0.0.0', port=80, debug=True)

