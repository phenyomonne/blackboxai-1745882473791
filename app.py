from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # For session management, in production use environment variable

# In-memory user storage for demo purposes
users = {
    # username: {password, approved, balance, language}
}

# Language translations
translations = {
    'en': {
        'welcome': 'Welcome to Women Financial House Botswana',
        'login': 'Login',
        'register': 'Register',
        'username': 'Username',
        'password': 'Password',
        'language': 'Language',
        'english': 'English',
        'setswana': 'Setswana',
        'logout': 'Logout',
        'account_approval_pending': 'Your account approval is pending.',
        'account_approved': 'Your account is approved.',
        'deposit': 'Deposit',
        'amount': 'Amount',
        'submit': 'Submit',
        'login_failed': 'Login failed. Please check your username and password.',
        'register_success': 'Registration successful. Please wait for account approval.',
        'already_registered': 'Username already registered.',
        'approval_required': 'Account approval required to access this page.',
        'deposit_success': 'Deposit successful. Your new balance is: ',
        'select_language': 'Select Language',
        'home': 'Home',
        'approve_account': 'Approve Account',
        'admin_login': 'Admin Login',
        'admin_password': 'Admin Password',
        'admin_login_failed': 'Admin login failed.',
        'pending_accounts': 'Pending Accounts',
        'approve': 'Approve',
        'no_pending_accounts': 'No pending accounts.',
    },
    'ts': {
        'welcome': 'Rea go amogela mo Women Financial House Botswana',
        'login': 'Kena',
        'register': 'Ikwadise',
        'username': 'Leina la mošomi',
        'password': 'Phasewete',
        'language': 'Puo',
        'english': 'Sekgoa',
        'setswana': 'Setswana',
        'logout': 'Tswalela',
        'account_approval_pending': 'Tlhahlobo ya akhaonto ya gago e ntse e le mo tseleng.',
        'account_approved': 'Akhaonto ya gago e amogetswe.',
        'deposit': 'Bea chelete',
        'amount': 'Chelete',
        'submit': 'Romela',
        'login_failed': 'Go tsena go paletswe. Lekola leina la mošomi le phasewete.',
        'register_success': 'Ikwadiso e atlegile. Tswelela o letetse tlhahlobo ya akhaonto.',
        'already_registered': 'Leina la mošomi le setse le ngwadilwe.',
        'approval_required': 'Tlhahlobo ya akhaonto e tlhokega go tsena mo lekgotleng leno.',
        'deposit_success': 'Go bea chelete go atlegile. Tekanyo ya gago e ntšha ke: ',
        'select_language': 'Kgetha Puo',
        'home': 'Lehae',
        'approve_account': 'Amohela Akhaonto',
        'admin_login': 'Kena bjalo ka Molaodi',
        'admin_password': 'Phasewete ya Molaodi',
        'admin_login_failed': 'Go tsena bjalo ka molaodi go paletswe.',
        'pending_accounts': 'Dikhaonto tse di letleletsweng',
        'approve': 'Amohela',
        'no_pending_accounts': 'Ga go na dikhaonto tse di letleletsweng.',
    }
}

def get_translation(key):
    lang = session.get('lang', 'en')
    return translations.get(lang, translations['en']).get(key, key)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def approval_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        username = session.get('username')
        if not username or not users.get(username, {}).get('approved', False):
            return render_template('approval_pending.html', t=get_translation)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html', t=get_translation)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in translations:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)
        if user and user['password'] == password:
            session['username'] = username
            session['lang'] = user.get('language', 'en')
            return redirect(url_for('dashboard'))
        else:
            error = get_translation('login_failed')
            return render_template('login.html', error=error, t=get_translation)
    return render_template('login.html', t=get_translation)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        language = request.form.get('language', 'en')
        if username in users:
            error = get_translation('already_registered')
            return render_template('register.html', error=error, t=get_translation)
        users[username] = {'password': password, 'approved': False, 'balance': 0, 'language': language}
        session['username'] = username
        session['lang'] = language
        message = get_translation('register_success')
        return render_template('approval_pending.html', message=message, t=get_translation)
    return render_template('register.html', t=get_translation)

@app.route('/dashboard')
@login_required
def dashboard():
    username = session['username']
    user = users.get(username)
    if not user['approved']:
        return render_template('approval_pending.html', t=get_translation)
    return render_template('dashboard.html', balance=user['balance'], t=get_translation)

@app.route('/deposit', methods=['GET', 'POST'])
@login_required
@approval_required
def deposit():
    if request.method == 'POST':
        amount = request.form.get('amount')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except:
            error = "Invalid amount"
            return render_template('deposit.html', error=error, t=get_translation)
        username = session['username']
        users[username]['balance'] += amount
        message = get_translation('deposit_success') + f"{users[username]['balance']}"
        return render_template('dashboard.html', message=message, balance=users[username]['balance'], t=get_translation)
    return render_template('deposit.html', t=get_translation)

# Simple admin login for approving accounts
ADMIN_PASSWORD = 'admin123'

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = get_translation('admin_login_failed')
            return render_template('admin_login.html', error=error, t=get_translation)
    return render_template('admin_login.html', t=get_translation)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    pending_users = [u for u, info in users.items() if not info['approved']]
    return render_template('admin_dashboard.html', pending_users=pending_users, t=get_translation)

@app.route('/admin/approve/<username>')
@admin_required
def approve_user(username):
    if username in users:
        users[username]['approved'] = True
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
