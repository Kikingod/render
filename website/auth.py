from flask import Blueprint, render_template, request , flash, url_for, redirect, jsonify, current_app, session
from .models import User, Note, Count, Count_anonymous
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import pandas as pd
from .help import ai
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from . import create_app





scheduler = BackgroundScheduler()

auth = Blueprint('auth', __name__)
scheduler.start()


@auth.route('/login',methods= ['POST','GET'] )
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email= email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('log in succesfolu', category='sucess')
                login_user(user, remember=True)#if server running user is logged
                
                return redirect(url_for('auth.home1'))
            else:
                flash('incoret password', category='error')
        else:
            flash('eail does not exist', category='error')
        
    return render_template('login.html', user=current_user)


@auth.route('/logout', methods= ['POST', 'GET'])
@login_required#dokud nejsi logged tak jsem nemuyes
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/signup',methods= ['POST', 'GET'])
def signin():
    if request.method == 'POST':#when i press submit button
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1= request.form.get('password1')
        password2= request.form.get('password2')
        
        user = User.query.filter_by(email= email).first()
        
        # if info is valid
        if user:
            flash('email alreade exist', category='error')
        elif len(email) < 4:
            flash('email must be greater than four charakters', category='error')
        elif len(first_name) <2:
            flash('there must be at least 3 charakters', category='error')
        elif password1 != password2:
            flash('eamil arent same', category='error')
        elif len(password1) <7:
            flash('password must be at least 8 charakters', category='error')
        else:
            new_user = User(email=email, first_name=first_name, password = generate_password_hash(password1, method='pbkdf2:sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('account craeted!!', category='success')
            login_user(new_user, remember=True)#if server running user is logged
            new_u = Count(data=1, user_id= current_user.id)
            db.session.add(new_u)
            db.session.commit()
            return redirect(url_for('auth.home1'))
            
    return render_template('signup.html', user=current_user)



async def get_response(question):
    return await asyncio.to_thread(ai, question)

@auth.route('/ai', methods=['POST', 'GET'])
def home1():
    return render_template('ai.html', user = current_user)


            
            
                 
            


@auth.route('/get', methods = ['GET', 'POST'])


def chat():
    
    def schedule():
        app = create_app()
        print(scheduler.get_jobs())
        with app.app_context():
            user2 =  Count.query.all()
            for user3 in user2:
                user3.data = 0
            db.session.commit()
            print('data = 0')
            
            
    def schedule_anonymouse():
        app = create_app()
        with app.app_context():
            row_count = db.session.query(Count_anonymous).count()
            if row_count != 0:
                db.session.query(Count_anonymous).delete()
                db.session.commit()
                print('deleted')
        

    if current_user.is_authenticated:
        if not scheduler.get_job('schedule'):
            scheduler.add_job(schedule, 'interval', minutes=1, id='schedule')
        
        usr = Count.query.filter_by(id=current_user.id).first()
        if usr == None:
            user = Count(data=1, user_id = current_user.id)
            db.session.add(user)
            db.session.commit()
        else:
            usr.data +=1
            db.session.commit()

        if usr.data >5:
            return render_template('home.html', user = current_user)
        else:
            msg = request.form["msg"]
            input = msg
            return ai(input, current_user)
    else:
        if not scheduler.get_job('schedule_anonymous'):
            scheduler.add_job(schedule_anonymouse, 'interval', minutes=1, id= 'schedule_anonymous')
        
        anonymous_user = Count_anonymous.query.filter_by(user_id=session['user_id']).first()
        if anonymous_user == None:
            user = Count_anonymous(data=1, user_id = session['user_id'])
            db.session.add(user)
            db.session.commit()
            msg = request.form["msg"]
            input = msg
            return ai(input,session['user_id'] )
        else:
            anonymous_user.data +=1
            db.session.commit()
        if anonymous_user.data >5:
            return render_template('home.html', user = current_user)
        else:
            msg = request.form["msg"]
            input = msg
            return ai(input,session['user_id'] )





