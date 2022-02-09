from flask import Flask,session,request,render_template,redirect,flash
from flask_debugtoolbar import DebugToolbarExtension
from models import db,connect_db,User,MedicalCenter,UserMedicalCenter
from forms import RegisterUserForm,LoginUserForm,EditEmail,EditTitle,EditPassword,DeleteAccountForm
from flask_bcrypt import Bcrypt
from datetime import date
from sqlalchemy.exc import IntegrityError
from geopy.geocoders import Nominatim

import requests
import os,sys

app = Flask(__name__)
#os.environ.get('DATABASE_URL').replace("://","ql://",1) or postgresql:///ems_gps_db
app.config["SQLALCHEMY_DATABASE_URI"] ="postgresql:///ems_gps_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
app.config["SQLALCHEMY_ECHO"]=True
app.config['SECRET_KEY']=os.environ.get('SECRET_KEY',os.urandom(30))
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"]=False

debug = DebugToolbarExtension(app)


connect_db(app)

bcrypt = Bcrypt()

today_date = date.today()

url_news = "https://bing-news-search1.p.rapidapi.com/news"

querystring = {"safeSearch":"Off","textFormat":"Raw"}

headers = {
    'x-bingapis-sdk': "true",
    'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
    'x-rapidapi-key': "d679a166f2msh7b54a2db9eea6c3p124dc4jsna3a4150de9b1"
    }

response = requests.request("GET", url_news, headers=headers, params=querystring)

curr_user_coords = []
stringlest_coords = []
hospitals_located = []

def clear_hospitals_located():
    return hospitals_located.clear()





def get_medical_center_data():
    url_geo = f"https://api.mapbox.com/geocoding/v5/mapbox.places/hospital.json?type=poi&proximity={curr_user_coords[0]}&limit=20&access_token=pk.eyJ1IjoiZ3JleW1lbmV6IiwiYSI6ImNrdm0xaXkyNDNhcjUydXFpazZoN3dzejEifQ.3UPkaylDPQMh9yeUMxiLUw"
    res = requests.get(url_geo)
    data = res.json()
    # print('##############################')
    # print(data)
    # print('##############################')
    # print('##############################')
    place_address_list = []
    facility_name_list = []
    category_list = []
    coordinates_list = []
    for d in data['features']:
        hospitals_located.append(d)
        place_address = d['place_name']
        facility_name = d['text']
        category =d['properties']['category']
        coordinates = d['geometry']['coordinates']
        place_address_list.append(place_address)
        facility_name_list.append(facility_name)
        category_list.append(category)
        coordinates_list.append(coordinates)
        med_centers = [MedicalCenter(place_address=p,facility_name=f,category=ca,coordinates=co) for p,f,ca,co in zip(place_address_list,facility_name_list,category_list,coordinates_list)]
    return db.session.add_all(med_centers)
        # print('*****************')
        # print(place_address_list)
        # print('*****************')
    
    
    
    # for d in data['features']:
    #     # hospitals_located.append(d)
        
    #     place_address = d['place_name']
    #     facility_name = d['text']
    #     # print('##############################')
    #     # print(d)
    #     # print('##############################')
        
    #     category = d['properties']['category']
    #     coordinates = d['geometry']['coordinates']

    #     place_address_list.append(place_address)
    #     facility_name_list.append(facility_name)
    #     category_list.append(category)
    #     coordinates_list.append(coordinates)
    #     med_centers = [MedicalCenter(place_address=p,facility_name=f,category=ca,coordinates=co) for p,f,ca,co in zip(place_address_list,facility_name_list,category_list,coordinates_list)]
    #     return db.session.add_all(med_centers)
# @app.route('/')
# def begin():
#     if 'user_id' in session:
#         curr_user = User.query.get_or_404(session['user_id'])
#         return redirect('/profile')
#     return render_template('begin.html')


@app.route('/')
def main():
    if 'user_id' in session:
        curr_user = User.query.get_or_404(session['user_id'])
        return redirect('/profile')
    return render_template('main.html')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterUserForm()
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        title = form.title.data
        email = form.email.data
        password = form.password.data
        
        try:
            new_user = User.register(first_name,last_name,title,email,password)
            db.session.add(new_user)
            db.session.commit()
            session['user_id'] = new_user.id
            return redirect('/profile')
        except Exception as e:
            print('##### BEFORE #####')
            print(e)
            print('##### AFTER #####')
            form.email.errors.append('Email already exists.')
            return render_template('register.html',form=form)
    print("Not validated")
    return render_template('register.html',form=form)

@app.route('/login',methods=['GET','POST'])
def login_user():
    form = LoginUserForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        auth_user = User.auth(email,password)
        if auth_user:
            session['user_id'] = auth_user.id
            return redirect('/profile')
        else:
            form.email.errors = ['Invalid Email/Password']
    return render_template('loginForm.html',form=form)

@app.route('/profile')
def profile_main():
    if 'user_id' in session:
        results = response.json()['value']
        curr_user = User.query.get_or_404(session['user_id'])
        return render_template('/users/profile_main.html',curr_user=curr_user,results=results,today_date=today_date)
    else:
        return redirect('/')

@app.route('/logout')
def user_logout():
    if 'user_id' in session:
        session.pop('user_id')
        return(redirect('/'))
    else:
        return(redirect('/'))
        

@app.route("/emerg-doc")
def search_results():
    if 'user_id' in session:
        curr_user = User.query.get_or_404(session['user_id'])
        coords = request.args.get('coords')
        curr_user_coords.append(coords)
        print('########################')
        print(coords)
        print('########################')
        print(curr_user_coords)
        user_centers = curr_user.user_medical_center
        saved_data = len(user_centers)
        return render_template('/users/emerg_doc.html',curr_user=curr_user,user_centers=user_centers,saved_data=saved_data)
    else:
        return redirect('/')

@app.route('/emerg-doc/results')
def test():
    if 'user_id' in session:
        clear_hospitals_located()
        
        curr_user = User.query.get_or_404(session['user_id'])
        curr_loc = curr_user_coords[0]
        
        user_centers = curr_user.user_medical_center
        saved_data = len(user_centers)
        get_medical_center_data()
        try:
            db.session.commit()
            
        except IntegrityError:
            db.session.rollback()
            return render_template('/users/emerg_doc_results.html',curr_loc=curr_loc,hospitals_located=hospitals_located,curr_user=curr_user,user_centers=user_centers,saved_data=saved_data)
        return render_template('/users/emerg_doc_results.html',curr_loc=curr_loc,hospitals_located=hospitals_located,curr_user=curr_user,user_centers=user_centers)
    else:
        return redirect('/')

@app.route('/save/<place_name>',methods=['POST'])
def save(place_name):
    if 'user_id' in session:
        try:
            medical_center_to_save = MedicalCenter.query.filter(MedicalCenter.place_address == place_name).first()
            saved_center = UserMedicalCenter(user_id=session['user_id'],medical_center_id=medical_center_to_save.id)

            db.session.add(saved_center)
            db.session.commit()
            flash('Saved!','success')
            return redirect('/emerg-doc/results')
        except IntegrityError:
            flash("Already saved!",'warning')
            return redirect('/emerg-doc/results')
    else:
        return redirect('/')

@app.route('/delete/<facility_id>',methods=['POST'])
def delete_facility(facility_id):
    if 'user_id' in session:
        facility = UserMedicalCenter.query.filter(UserMedicalCenter.medical_center_id == facility_id).first()
        db.session.delete(facility)
        db.session.commit()
        return redirect('/emerg-doc')
    else:
        return redirect('/')

@app.route('/settings')
def settings():
    curr_user = User.query.get_or_404(session['user_id'])
    return render_template('/users/account_settings.html',curr_user=curr_user)


@app.route('/settings/edit-email',methods=['GET','POST'])
def edit_email():
    curr_user = User.query.get_or_404(session['user_id'])
    form = EditEmail()
    if 'user_id' in session:
        if form.validate_on_submit():
            new_email = form.new_email.data
            password = form.password.data
            password_confirm = form.password_confirm.data
            if password == password_confirm:
                auth_user = curr_user.auth(curr_user.email,password_confirm)
                if auth_user:
                    auth_user.email = new_email
                    db.session.commit()
                    flash("Email changed!","success")
                    return redirect('/settings/edit-email')
                else:
                    form.password_confirm.errors = ['Invalid Password']
            else:
                form.password_confirm.errors = ['Passwords Do Not Match']
        return render_template('/users/edit_email.html',curr_user=curr_user,form=form)
    return redirect('/')

@app.route('/settings/edit-title',methods=['GET','POST'])
def edit_title():
    curr_user = User.query.get_or_404(session['user_id'])
    form = EditTitle()
    if 'user_id' in session:
        if form.validate_on_submit():
            new_title = form.new_title.data
            password = form.password.data
            password_confirm = form.password_confirm.data
            if password == password_confirm:
                auth_user = curr_user.auth(curr_user.email,password_confirm)
                if auth_user:
                    auth_user.title = new_title
                    db.session.commit()
                    flash("Title changed!","success")
                    return redirect('/settings/edit-title')
                else:
                    form.password_confirm.errors = ['Invalid Password']
            else:
                form.password_confirm.errors = ['Passwords Do Not Match']
        return render_template('/users/edit_title.html',curr_user=curr_user,form=form)
    return redirect('/')

@app.route('/settings/password-change',methods=['GET','POST'])
def edit_password():
    curr_user = User.query.get_or_404(session['user_id'])
    form = EditPassword()
    if 'user_id' in session:
        if form.validate_on_submit():
            curr_password = form.curr_password.data
            new_password = form.new_password.data
            new_password_confirm = form.new_password_confirm.data
            if new_password == new_password_confirm:
                if bcrypt.check_password_hash(curr_user.password,curr_password):
                
                    auth_user = curr_user.auth(curr_user.email,curr_password)
                    if auth_user:
                            
                        hashed = bcrypt.generate_password_hash(new_password)
                        hashed_pwd = hashed.decode('utf8')
                        auth_user.password = hashed_pwd
                        db.session.commit()
                        flash("Password changed!","success")
                        return redirect('/settings/password-change')
                else:
                    form.curr_password.errors = ["Invalid Password"]        
            else:
                form.new_password_confirm.errors = ['Passwords Do Not Match']
        return render_template('/users/edit_password.html',curr_user=curr_user,form=form)
    return redirect('/')


@app.route('/settings/delete',methods=['GET','POST'])
def delete_account():
    curr_user = User.query.get_or_404(session['user_id'])
    form = DeleteAccountForm()
    if 'user_id' in session:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            password_confirm = form.password_confirm.data
            if password == password_confirm:
                auth_user = curr_user.auth(curr_user.email,password_confirm)
                if auth_user and email == curr_user.email:
                    session.pop('user_id')
                    db.session.delete(auth_user)
                    db.session.commit()
                    return redirect('/')
                elif not auth_user:
                    form.password_confirm.errors = ['Invalid Password']
                elif email != curr_user.email:
                    form.email.errors = ['Invalid email']
        return render_template('/users/delete_account.html',curr_user=curr_user,form=form)
    return redirect('/')




    
