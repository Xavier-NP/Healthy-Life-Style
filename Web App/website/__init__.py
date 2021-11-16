from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

#Assigning Database Module
db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'GUMMYKKB'
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}" #Database Storage
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app) #Initializing the Database
    
   
    
    #Importing Routes
    from .views import views
    from .auth import auth
    
    #Setting Prefixes
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    #Check if Database file Exists
    from .models import User,Note
    create_database(app)
    
    #Initializing Data into Database
    init_Disabilities(app) # To be run without DEBUG MODE
    
    #Login Manager
    login_manager= LoginManager()
    login_manager.login_view = 'auth.login' #Redirects to login page if trying to access login_required routes
    login_manager.init_app(app)
    
    #Defining to the app on how to load a user
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    
    return app

#Initializing Disabilities
    
def init_Disabilities(app):
    from .models import Disability
    disability_names= ["Diabetes","Crutches"] #Ensure that name is EXACTLY THE SAME as checkbox name in sign_up.html
    with app.app_context():
        check = Disability.query.filter_by(id=1).first()
        if not check:
                for x in range(len(disability_names)):
                    new_disability = Disability(disName=disability_names[x])
                    db.session.add(new_disability)
                    db.session.commit()
        
    
        
#Creating Database
def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
        

        