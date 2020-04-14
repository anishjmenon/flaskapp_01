from flask import Flask, render_template, url_for, flash, redirect, request
from forms import LoginForm, StockConfirmationForm
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

app = Flask(__name__)

app.config['SECRET_KEY'] = '9e5fa42d176d5b2b0924f825e127f1bf'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stkcfm.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    stock = db.relationship('Stock', backref='creator', lazy=True)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}')"

class Materialmast(db.Model):
    material_num = db.Column(db.Integer, primary_key=True)
    material_desc = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Materialmast('{self.material_num}', '{self.material_desc}')"

class Stock(db.Model):
    material_num = db.Column(db.Integer, db.ForeignKey('materialmast.material_num') ,primary_key=True )
    date_posted = db.Column(db.DateTime, primary_key= True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),primary_key=True)
    quantity = db.Column(db.Float)

    def __repr__(self):
        return f"Stock('{self.material_num}', '{self.date_posted}', '{self.quantity}')"

@app.route("/home", methods=['GET','POST'])
@login_required
def home():
    stkform = StockConfirmationForm()
    stkform.material.choices = [(mat.material_num, mat.material_desc) for mat in Materialmast.query.all()]
    if stkform.validate_on_submit():
        quantity = stkform.quantity.data
        mat = Materialmast.query.filter_by(material_num=stkform.material.data).first()
        material = mat.material_num
        # material = mat
        user_id = current_user.id
        #material = Materialmast.query.filter_by(material_num=stkform.material.data).first()
        if quantity:
            stock = Stock(material_num=material,user_id=user_id,quantity=quantity)
            db.session.add(stock)
            db.session.commit()
            flash(f'Posted quantity {quantity} for material {mat.material_desc}', 'success')
            # flash(f'Posted quantity {quantity} for material {material} by user {user_id}', 'success')
            return redirect(url_for('home'))
    return render_template('home.html', title='Home', form=stkform)

@app.route("/", methods=['GET','POST'])
@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    lform =  LoginForm()
    if lform.validate_on_submit():
        user = User.query.filter_by(email=lform.email.data).first()
        if user and (user.password == lform.password.data):
            login_user(user,lform.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=lform)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)