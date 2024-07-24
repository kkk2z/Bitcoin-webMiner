from quart import Quart, render_template, request, redirect, url_for, flash
from quart_sqlalchemy import SQLAlchemy
from quart_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import aiohttp
from plyer import notification

app = Quart(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    mining_address = db.Column(db.String(150), nullable=True)
    balance = db.Column(db.Float, default=0.0)

@login_manager.user_loader
async def load_user(user_id):
    return await User.query.get(int(user_id))

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        form = await request.form
        username = form.get('username')
        password = form.get('password')
        user = await User.query.filter_by(username=username).first()
        if user and user.password == password:
            await login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login Unsuccessful. Please check username and password', 'danger')
    return await render_template('login.html')

@app.route('/dashboard')
@login_required
async def dashboard():
    return await render_template('dashboard.html', user=current_user)

@app.route('/set_address', methods=['POST'])
@login_required
async def set_address():
    form = await request.form
    address = form.get('address')
    current_user.mining_address = address
    await db.session.commit()
    flash('Mining address updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/average')
async def average_balance():
    total_balance_result = await db.session.execute('SELECT SUM(balance) FROM user')
    user_count_result = await db.session.execute('SELECT COUNT(*) FROM user')
    total_balance = total_balance_result.first()[0]
    user_count = user_count_result.first()[0]
    average = total_balance / user_count if user_count > 0 else 0
    return f'Average Balance: {average} BTC'

async def send_rewards(user, amount):
    async with aiohttp.ClientSession() as session:
        async with session.post('https://example.com/api/send', json={
            'address': user.mining_address,
            'amount': amount
        }) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception('Failed to send rewards')

def send_notification():
    notification.notify(
        title='Mining Milestone Reached',
        message='You have reached 100 BTC in mining!',
        app_name='My Mining Site'
    )

if __name__ == '__main__':
    app.run(debug=True)
