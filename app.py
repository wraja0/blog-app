'''
Lightweight blog application with hashed user authentication and secure token verification for data persistance.
Users can register and login to their accounts to create blog posts. Blog posts belonging to them are able to be
edited and deleted. Only required data persists through the user session.
'''
import time
from datetime import datetime,timedelta
from functools import wraps
import secrets
from flask import Flask, redirect, render_template, request, url_for,session
from werkzeug import exceptions as werkzeug_exceptions
import jwt
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from psycopg2 import IntegrityError

#APP CONFIG
app = Flask(__name__)
app.config['SECRET_KEY']= secrets.token_urlsafe(12)
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:blog-user@db/blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

#FLASK_SQLALCHEMY ORM SETUP

db = SQLAlchemy(app)
retries = 5
while (retries !=0):
    try:
        db.create_all()
        break
    except(Exception) as e:
        retries -=1
        print(f'Retries left : {retries}')
        print(e)
        time.sleep(5)
# USER MODEL
class User(db.Model):
    '''
    Model for the app users table
    Model includes id PK as an integer
    Username as a string
    Password as a Binary
    admin_tatus as a Boolean
    A one to many reltation with the Posts model called posts
    '''
    __tablename__='users'
    id = db.Column(db.Integer, primary_key=True)
    username =(db.Column)(db.String(30),unique=True,nullable=False)
    password=(db.Column)(db.LargeBinary,nullable=False)
    email = (db.Column)(db.String(40),unique=True,nullable=False)
    admin_status=(db.Column)(db.Boolean,nullable=True)
    posts = (db.relationship('Post', backref='user', lazy=True))
    def __repr__(self):
        return f'<User Model with username {self.username}>'
# POST MODEL
class Post(db.Model):
    '''
    Model for the app posts table
    Model includes id PK as an integer
    Title as a string max-length 65 characters
    Body as a string max-length 500 characters
    Timestamp as a Date
    user_id as a FK showing relation to the owner user
    '''
    __tablename__='posts'
    id = db.Column(db.Integer, primary_key=True)
    title =(db.Column)(db.String(65),nullable=False)
    body  = (db.Column)(db.String(500),nullable=False)
    user_id= (db.Column)(db.Integer, db.ForeignKey('users.id'))
    timestamp = (db.Column)(db.Date, nullable=False)
    def __repr__(self):
        return f'<Post Model with id {self.id}>'

# MIDDLEWARE
def auth_token(func):
    '''
    Middleware function used to determine if has a jwt authenticating login.
    If middleware detects an invalid,expired, or nonexistant token, redirect to login
    '''
    @wraps(func)
    def decorated(*args,**kwargs):
        '''
        Decorater function to wrap middleware
        '''
        try :
            # Verify token is not null
            if 'token' not in session:
                raise werkzeug_exceptions.Forbidden

            # Number of things can go wrong here
            #Test for jwt here
            data = jwt.decode(session['token'],app.config['SECRET_KEY'],algorithms=["HS256"])
            if not data or not 'user_login_status' in data or data['user_login_status'] is False:
                raise werkzeug_exceptions.Unauthorized
            return func(*args,**kwargs)
        except(werkzeug_exceptions.Forbidden) as error:
            print(error)
            print('Client is missing token')
            return render_template('login.html'),401
        except(werkzeug_exceptions.Unauthorized) as error:
            print(error)
            print('Unauthorized login')
            return render_template('login.html'),401
    return decorated

# ROUTES

@app.route('/')
def root():
    '''
    Root directory route.
    Re-routed to '/home'
    '''
    return redirect(url_for('home'))

@app.route('/home')

def home():
    '''
    Home route
    Queries databse for all posts then checks whether session 'user_login_status' is True and a jwt exists.
    If it is true and a jwt exists the token is decoded and the username is configured with the page to match
    ownership to posts. If either fails load without post ownership and create post features.
    '''
    try :
        # Query all Posts
        posts= db.session.query(Post).order_by(Post.timestamp)

        # If not logged in render template without logged in features
        if 'user_login_status' not in session or session['user_login_status'] is False :
            return render_template('home.html',posts=posts,loggedin=False,username='guest')

        # If user is logged in check for token
        if 'token' not in session:
            raise werkzeug_exceptions.Unauthorized
        # Decode token ... I may expect some errors here
        # IMPLEMENT TESTS HERE #
        data = jwt.decode(session['token'],app.config['SECRET_KEY'],algorithms=["HS256"])
        username = data['username']
        return render_template('home.html',posts=posts,loggedin=True,username=username)
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print ("User with user login status true does not have a token in session storage")
        return render_template('home.html',posts=posts,loggedin=False,username ='guest')
    except(jwt.ExpiredSignatureError) as error :
        print(error)
        print('User token has expired!')
        return render_template('home.html',posts=posts,loggedin=False,username ='guest')

@app.route('/about')

def about():
    '''
    About route. Simply render the about page. No other logic present.
    '''
    return render_template('about.html')

@app.route('/login', methods=['GET','POST'])
def login():
    '''
    Login route with post and get methods
    Get method renders login page no other logic
    Post method checks for proper data, if any is missing, page re-renders with feedback
    If no data is missing attempts to look up the user. If none is found re-render with feedback
    If a user is found but the password hash is not comparable, re-render with feedback.
    If authentication is successful. Set session token data and redirect to home route.
    '''
    try:
        # GET REQUEST
        if request.method=='GET':
            return render_template('login.html')

        # POST REQUEST

        # Verify login form data is not null
        if 'email' not in request.form or 'password' not in request.form:
            raise werkzeug_exceptions.NotAcceptable
        user_email = request.form['email']
        password = request.form['password']

         # Verify login form data is not empty string
        if user_email =='' or password=='':
            raise werkzeug_exceptions.NotAcceptable

        # Verify user exists in User table
        query_user = db.session.query(User).filter_by(email=user_email).first()
        if not query_user:
            raise IntegrityError

        # Authenticate password
        if not bcrypt.checkpw(password.encode('utf-8'),query_user.password):
            raise werkzeug_exceptions.Unauthorized
        # ENCODE TOKEN
        token = jwt.encode({
            'username':query_user.username,
            'exp': datetime.utcnow() + timedelta(hours=3),
            'user_login_status': True,
        },app.config['SECRET_KEY'],algorithm="HS256")

        # SET SESSION ENV
        session['token'] = token
        session['user_login_status'] = True

        # Go to admin page for admin users
        if query_user.admin_status is True:
            session['admin_status'] = True
            query_all_users= db.session.query(User.username,User.email).all()
            return render_template('admin.html',users=query_all_users),302
        #Else redirect to home page
        return redirect(url_for('home'))
    except(werkzeug_exceptions.NotAcceptable) as error:
        print (error)
        print('Post request failed because either the form data was null or an empty string')
        return render_template('login.html',error='Please complete all fields to login'),406
    except(IntegrityError) as error:
        print(error)
        print("Post request failed No user exists by that email")
        return render_template('login.html',error='Username and password could not be verified'),401
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print("Post request failed Username and password could not be verified")
        return render_template('login.html',error='Username and password could not verified'),401
@app.route('/register',methods=['POST','GET'])
def register():
    '''
    Register route, accepts POST and GET methods.
    A get method yields the register page. No other logic
    A post method first checks if all required fields are not null and not empty
    Then checks if the email address ends in .com. If not : provide feedback
    Then checks for matching password and confirm password fields. If failure provide feedback
    If success check if username or email exists in databse. If it does provide feedback
    Finally check if the password is longer than 6 characters if it is. Add new user to databse and
    redirect to login page. Otherwise provide error feedback
    '''
    try :
        # FOR GET REQUEST RENDER TEMPLATE
        if request.method=='GET':
            return render_template('register.html')

        # Ensure all the required form data is non null
        if not(
        'username' in request.form and 'password1' in request.form
        and 'password2' in request.form and 'email' in request.form):
            raise werkzeug_exceptions.NotAcceptable
        user_name = request.form['username']
        user_password =request.form['password1']
        user_email = request.form['email']

        # Verify the user_name or password or email are not empty strings
        if user_name=='' or user_password=='' or user_email=='':
            raise werkzeug_exceptions.NotAcceptable

        # Verify the email ends in .com
        if user_email[-4:] != '.com':
            raise werkzeug_exceptions.BadRequest

        # Verify the user typed in the same password twice
        if request.form['password1'] != request.form['password2']:
            raise werkzeug_exceptions.Forbidden
        # Verify the password is at least six characters
        if len(user_password) < 6:
            raise werkzeug_exceptions.Unauthorized
         # Verify email is not already with a user in db
        if db.session.query(User).filter_by(email=user_email).count()!=0:
            raise werkzeug_exceptions.Conflict
        # Verify username is not taken
        if db.session.query(User).filter_by(username=user_name).count()!=0:
            raise IntegrityError

        #Hash password and create user
        user_password = bcrypt.hashpw(user_password.encode('utf-8'),bcrypt.gensalt())
        new_user = User(username=user_name,password=user_password,email=user_email)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    except(werkzeug_exceptions.NotAcceptable) as error:
        print (error)
        print('/login POST request failed. Either the form data was null or empty strings')
        return render_template('register.html',error='Please do not leave any fields blank'),406
    except(werkzeug_exceptions.Forbidden) as error:
        print(error)
        print('User POST request failed. Passwords do not match')
        return render_template('register.html',error='The passwords must match'),406
    except(werkzeug_exceptions.BadRequest) as error:
        print(error)
        print('User POST request failed. Email does not end in .com suffix')
        return render_template('register.html',error='Please enter a valid E-mail address'),406
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print('The POST request failed. The password is too short ')
        return render_template('register.html',error='The password must be at least six characters'),406
    except(werkzeug_exceptions.Conflict) as error:
        print(error)
        print("User POST request failed email already exists with an account on database")
        return render_template('register.html',error='E-mail is already registered please sign in'),406
    except(IntegrityError) as error:
        print(error)
        print(f"User POST request failed. The username {user_name} already exists")
        return render_template('register.html',error='Username is already taken'),406

@app.route('/logout')
def logout():
    '''
    Logout route. Simply refreshes the session by reconfiguring the secret key. Users are logged out and
    users are redirected to home page.
    '''
    app.config['SECRET_KEY'] = secrets.token_urlsafe(12)
    return redirect(url_for('home'))

@app.route('/posts/new',methods=['POST','GET'])
@auth_token
def create_post():
    '''
    Protected create post route.
    After running middleware, check again for login status in session. Redirect to login in case of breach.
    Then if GET request simply render create post page.
    If POST request Verify the data is not null and not empty strings. If failure provide feedback otherwise
    decode token to retreive username and create new post with Post class. Bind post to user and add post to
    databse
    '''
    try :
        #Verify user is logged in
        if 'user_login_status' not in session or session['user_login_status'] is not True:
            raise werkzeug_exceptions.Unauthorized

        # GET REQUEST
        if request.method == 'GET':
            return render_template('create_post.html')
        #POST REQUEST
        # Verify title and body are not null
        if not('title' in request.form and 'body' in request.form):
            raise werkzeug_exceptions.NotAcceptable

        title=request.form['title']
        body=request.form['body']

        #Verify title and body are not empty strings
        if  title == '' or body == '':
            raise werkzeug_exceptions.NotAcceptable

        # No need to test this function will only run after already being decoded
        data = jwt.decode(session['token'],app.config['SECRET_KEY'],algorithms=["HS256"])
        username = data['username']
        user = db.session.query(User).filter_by(username=username).first()
        new_post = Post(title=title,body=body,timestamp=datetime.utcnow())
        user.posts.append(new_post)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print('A user who has not logged in tried to post to the create_post route')
        return render_template('login'),401
    except(werkzeug_exceptions.NotAcceptable) as error:
        print(error)
        print('Post request failed. Either title or body was missing or null')
        return render_template('create_post.html',error='Please do not leave any fields blank'),406
@app.route('/posts/<int:postid>/delete')
@auth_token
def delete_post(postid):
    '''
    Protected delete route.
    After running middleware check once more for login status in session.
    Query the post to delete from the databse. If not found, re-render homepage.
    If found decode token and compare username in token to username relating to the post in database.
    If there is a breach redirect to login else delete the post from the databse.
    '''
    try :

        if 'user_login_status' not in session or session['user_login_status'] is not True:
            raise werkzeug_exceptions.Unauthorized

        post_to_delete = db.session.query(Post).get(postid)

        if not post_to_delete:
            raise werkzeug_exceptions.NotFound
        data = jwt.decode(session['token'],app.config['SECRET_KEY'],algorithms=["HS256"])
        if post_to_delete.user.username != data['username']:
            raise werkzeug_exceptions.Forbidden
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect(url_for('home'))
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print(f" User {request.method} request failed User is not logged in")
        return render_template('login'),401
    except(werkzeug_exceptions.NotFound) as error:
        print(error)
        print(f"User {request.method} request failed No post with id : {postid} exists")
        return render_template('home.html'),404
    except(werkzeug_exceptions.Forbidden) as error:
        print(error)
        print(f" User {request.method} request failed User is attempting to delete a post that does not belong to them")
        return render_template('login.html'),403
@app.route('/posts/<int:postid>/edit',methods=['GET','POST'])
@auth_token
def update_post(postid):
    '''
    Protected update route.
    After running middleware check again for login status in session.
    Then query the post to update and if GET request render edit post page with queries post.
    If post request, first verify required fields are non null and not empty strings. If otherwise provide
    feedback. Then decode token and compare username in token to username relating to the post queried.
    If unauthorized redirect to login page. If authorized update the data in the databse and redirect to home.
    '''
    try :

        if 'user_login_status' not in session or session['user_login_status'] is not True:
            raise werkzeug_exceptions.Unauthorized

        post_to_update = db.session.query(Post).get(postid)

        if not post_to_update:
            raise werkzeug_exceptions.NotFound

        if request.method == 'GET':
            return render_template('update_post.html',post=post_to_update)

        if not('title' in request.form and 'body' in request.form):
            raise werkzeug_exceptions.NotAcceptable

        title = request.form['title']
        body = request.form['body']

        if body=='' or title=='':
            raise werkzeug_exceptions.NotAcceptable

        data = jwt.decode(session['token'],app.config['SECRET_KEY'],algorithms=["HS256"])
        if data['username'] != post_to_update.user.username:
            raise werkzeug_exceptions.Forbidden

        post_to_update.title = title
        post_to_update.body = body
        db.session.commit()
        return redirect(url_for('home'))
    except(werkzeug_exceptions.Unauthorized) as error:
        print(error)
        print(f" User {request.method} request failed User is not logged in")
        return redirect(url_for('login',code=401,response=None))
    except(werkzeug_exceptions.NotFound) as error:
        print(error)
        print(f"User {request.method} request failed No post with id : {postid} exists")
        return render_template('home.html',error='Post could not be found'),404
    except(werkzeug_exceptions.NotAcceptable) as error:
        print(error)
        print('Post request failed. Either title or body was missing or null')
        return render_template('update_post.html',error='Please do not leave any fields blank',post=post_to_update),406
    except(werkzeug_exceptions.Forbidden) as error:
        print(error)
        print("Update request failed. User is attempting to update a post that does not belong to them")
        return render_template('login.html'),403
if __name__=='__main__':
    app.run(None,3000,True)
