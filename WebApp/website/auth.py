#Authenticated Routes for Website i.e. sites requiring authentication

from calendar import month
import re
from flask import Blueprint,render_template,request,flash,redirect,url_for
from flask.helpers import send_file
import flask_restful
from sqlalchemy import select
from sqlalchemy.sql.functions import user
from .models import Disability, Doctor,Patient, User,CalsBMI
import hashlib
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import datetime
import matplotlib.pyplot as plt
import plotly
from matplotlib.gridspec import GridSpec
from io import BytesIO, StringIO
import base64
import mpld3
import datetime as dt
from sqlalchemy import desc
from flask_mail import Message




auth = Blueprint('auth',__name__)
NoneType=type(None)
pw = hashlib.sha256()
##Routes

#Redirect
@auth.route('/')
@login_required
def reLink():
    return render_template("home.html",user=current_user)
        

#Login Route
@auth.route('/login',methods=['GET','POST'])
def login():
    if request.method =='POST':
        # Get Data from HTML
        email = request.form.get('email')
        password = request.form.get('password')
        
        #Check if user exists on the Database using email
        user = User.query.filter_by(email=email).first()
        if user:
            if check_pw(user,password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True) #Allows for website to remember user is logged in the current session
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect Password! Please try again!', category='error')
        else:
            flash("Email does not exist!",category = 'error')
            
    return render_template("login.html",user = current_user)

#Logout Route
@auth.route('/logout')
@login_required #Ensures that route is only accessible if user is logged in
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

#Sign-up Route
@auth.route('/sign-up',methods=['GET','POST'])
def sign_up():
    if request.method =='POST':
        # Get Data from HTML
        
        first_name= request.form.get('firstName')
        last_name= request.form.get('lastName')
        email= request.form.get('email')
        mobileNum = request.form.get('mobileNum')
        nric = request.form.get('nric')
        addr = request.form.get('addr')
        password1= request.form.get('password1')
        password2= request.form.get('password2')
        disabilities = request.form.getlist('disability')
        doctor = request.form.get('doctor')
        
        #Check for any errors and flash if there are
        user = Patient.query.filter_by(email=email).first()
        if user:
            flash('Email already exists',category='error')
        elif len(email)<4: #Check if email is has more than 3 alphanumeric
            flash('Email must be greater than 3 Characters.', category='error')
        elif len(first_name) <2: #check if first name has more than 1 letters
            flash('First Name must be more than 1 Character.', category='error')
        elif len(last_name) <2: #check if last name has more than 1 letters
            flash('Last Name must be more than 1 Character.', category='error')
        elif len(mobileNum)!=8 or (mobileNum.isnumeric()==False):#ensure number is 8 digits, mobile number is numeric
            flash('Enter a valid 8 digit mobile number', category = 'error')
        elif len(nric)!=9:#ensure ic entered is 9 char
            flash('Enter a valid NRIC/FIN')
        elif len(password1)<7: #Check if password is more than 7 alphanumeric
            flash('Password must be at least 7 Characters', category='error')
        elif password1 != password2: #Check if password and confirm password is the same
            flash('Passwords dont\'t match.', category='error')
        elif not disabilities: #Check if at least 1 disability is selected
            flash('Please select a disability!',category='error')
        else:
            pw.update(password1.encode("utf-8"))
            #Creating New user
            new_user = Patient(first_name=first_name,
                            last_name=last_name, 
                            email=email, 
                            mobileNum=mobileNum, 
                            nric=nric, addr=addr, 
                            password=pw.digest().hex(),
                            doctor_id=doctor
                            #role_id=1 # Setting all users that login to be Patients
                            )
            
            #Assigning disabilities to user
            for x in range(len(disabilities)):
                dist_name=Disability.query.filter_by(disName=disabilities[x]).first()
                new_user.disabilities.append(dist_name)
            
            
            #Adding created user to DB
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True) #Allows for website to remember user is logged in the current session
            flash("Account Created!", category="success")
            return redirect(url_for("views.home"))
            
    return render_template("sign_up.html", user = current_user)

#User-Info Route
@auth.route('/user-info')
@login_required
def userInfo():
    return render_template("user_info.html",user = current_user)



def getBMI(w,h):
    bmi = round((w/((h/100)**2)),2)
    return bmi
    


#Calculate BMI
@auth.route('/bmi',methods=['GET','POST'])
@login_required
def calBMI():#bmi = kg/m^2
    if request.method == 'POST' and request.form.get('weight').isnumeric() and request.form.get('height').isnumeric():
        w = float(request.form.get('weight'))
        h = float(request.form.get('height'))
        bmi = getBMI(w,h)

        return render_template("bmi.html",bmi = bmi,user=current_user)
    else:
        return render_template("bmi.html",bmi=0,user = current_user)


@auth.route('/calories',methods = ['GET','POST'])
@login_required
def calories():
    if request.method == 'POST' and request.form.get('weight')!="" and request.form.get('age')!=""and request.form.get('age')!="":
        w = float(request.form.get('weight'))
        h = float(request.form.get('height'))
        age = int(request.form.get('age'))
        gender = request.form.get('gender')
        activeness = request.form.get('activeness')
        bmr = 0
        calNeed = 0
        if gender == "male":
            bmr = 88.362 + (13.397*w)+(4.799*h)-(5.677*age)
        elif gender == "female":
            bmr = 447.593 + (9.247*w) + (3.098*h)-(4.330*age)
        if(activeness == "1"):
            calNeed = bmr*1.2
        elif(activeness == "2"):
            calNeed = bmr*1.37
        elif(activeness == "3"):
            calNeed = bmr*1.55
        elif(activeness=="4"):
            calNeed = bmr*1.725
        elif(activeness=="5"):
            calNeed = bmr*1.9
        calNeed = round(calNeed,2)
        bmi = getBMI(w,h)
    else:
        calNeed = 0
        bmi = 0

        #intake
    if request.method=="POST" and request.form.get("breakfast")!=NoneType and request.form.get("lunch")!=NoneType and request.form.get("dinner")!=NoneType: 
        chickenRice = 607 #https://www.healthhub.sg/live-healthy/165/healthy_cooking
        wontonNoodle = 409 #https://www.thestar.com.my/lifestyle/viewpoints/tell-me-about/2011/02/27/malaysian-calories
        duckRice = 673 #https://www.healthxchange.sg/food-nutrition/food-tips/best-worst-singapore-hawker-chinese-food-duck-rice-fishball-noodle


        #getting calories for the other food bOtherCalorie is for breakfast
        try:
            otherFoodB = float(request.form.get('bOtherCalorie'))#try to get the other food
        except:
            otherFoodB = 0 #if not, assign it to 0
        try:
            otherFoodL = float(request.form.get('lOtherCalorie'))
        except:
            otherFoodL = 0
        try:
            otherFoodD = float(request.form.get('dOtherCalorie'))
        except:
            otherFoodD = 0

        meal = [chickenRice,wontonNoodle,duckRice,otherFoodB,otherFoodL,otherFoodD]

        #Serving size in quantity
        try:
            bServing = int(request.form.get('bServing'))
        except:
            bServing = 1
        try:
            lServing = int(request.form.get('lServing'))
        except:
            lServing = 1
        try:
            dServing = int(request.form.get('dServing'))
        except:
            dServing=1
        ##

        try:
            breakfast = int(request.form.get('breakfast'))
            lunch = int(request.form.get('lunch'))
            dinner = int(request.form.get('dinner'))

            totalIntake = ((meal[breakfast]*bServing)+(meal[lunch]*lServing)+(meal[dinner]*dServing))
        except:
            totalIntake=0
    else:
        totalIntake=0
    if bmi!=0 and totalIntake!=0:
        dateNow = datetime.datetime.now().date()
        #dateNow=datetime.date(2022, 1, 1)#place data into the db to test (yyyy, mm, dd)
        exist = CalsBMI.query.order_by(CalsBMI.CalsBMIdate).filter_by(CalsBMIid = current_user.id).all()
        recorded = False#set it to false first
        if len(exist)==0:
            recorded = False
        else:
            try:
                if exist[-1].CalsBMIdate == dateNow:# if the date already exists
                    recorded = True
            except:
                recorded = False
        
        if recorded == True:#user has already recorded today
            flash(f'You can record BMI and Calories input once per day! [{exist[-1].calories} kcals and BMI of {exist[-1].bmi} recorded]',category='error')
        else:
            new_CalsBMI = CalsBMI(calories = totalIntake, bmi = bmi, CalsBMIdate = dateNow, CalsBMIid = current_user.id)
            db.session.add(new_CalsBMI)
            db.session.commit()
            flash('Your BMI and Calories input has been recorded',category='success')
    #if there is data input, scroll to the bottom
    scroll = True
    if calNeed == 0 and totalIntake == 0:
        scroll = False

    return render_template("calories.html",calNeed = calNeed, totalIntake = totalIntake,bmi=bmi,user = current_user,scroll = scroll)


@auth.route('/health-trend',methods = ['GET','POST'])
@login_required
def health_trend():
    dateList,caloriesList, bmiList,isEmpty = chooseData()
    if isEmpty == True:#if there is no data or too little data
        flash('You do not have enough data for generation of dashboard, an example of the dashboard will be shown instead',category='error')

    return render_template("health_trend.html",user = current_user, dateList = dateList,caloriesList = caloriesList,bmiList =bmiList)

@auth.route('/accidents',methods=['GET','POST'])
@login_required
def accidents():
    return render_template("accidents.html",user=current_user)


def chooseData(): #function get data from the database to use for visualisation
    dateList = []
    caloriesList = []
    bmiList = []
    isEmpty = False #condition to check if there is data recorded, set to false as default
    try:
        data = CalsBMI.query.order_by(CalsBMI.CalsBMIdate).filter_by(CalsBMIid = current_user.id).all()
        for i in data:#append date into list first
            dateList.append(i.CalsBMIdate)
            caloriesList.append(i.calories)
            bmiList.append(i.bmi)
    except:
        ""#the records does not exist
        
    if len(dateList) < 3:#if the length is less than 3
        isEmpty = True #the user does not have data recorded
        dateList = ['2021-2-1', '2021-3-1', '2021-4-1', '2021-5-1', '2021-6-1', '2021-7-1', 
        '2021-8-1', '2021-9-1', '2021-10-1', '2021-11-1', '2021-12-1', '2022-1-1', ]
        caloriesList=[1700,1800,1850,1900,2000,1940,1800,1860,1990,2000,2100,1900]
        bmiList=[19, 19.3, 19.5, 20, 21, 20.5, 19.1, 19.6, 20.1, 21.3,21.8,19.8]

    return dateList,caloriesList,bmiList,isEmpty


#Check User Password if correct Function
def check_pw(user,e_pw):
        ph = hashlib.sha256()
        ph.update(e_pw.encode("utf-8"))
        hashed_pw = ph.digest().hex()
        if user.password==hashed_pw:
            return True
        else:
            return False    
    
