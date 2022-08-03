import pytest
import secrets
import jwt
import bcrypt
from datetime import datetime, timedelta
from app import User, app, db, Post

@pytest.fixture(autouse=True)
def test_client():
    '''
    Configure a client session who is not logged in
    Add a user to implement login testing later
    Yeild the test client
    '''
    app.config['SECRET_KEY']= secrets.token_urlsafe(12)
    app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Qlammers3903@localhost/test_blog'
    db.drop_all()
    db.create_all()
    password = bcrypt.hashpw('123123'.encode('utf-8'),bcrypt.gensalt())
    test_user =User(username='admin122',email='testuser@gmail.com',password=password)
    db.session.add(test_user)
    db.session.commit() 
    with app.test_client() as testing_client:
        yield testing_client

@pytest.fixture(autouse=True)  
def test_loggedin_client():
    '''
    Confiugre a client session of a testuser who is logged in
    Add relavant data to test database to implent tests later, including two new users and 4 new posts
    Yield the logged in test client
    '''
    app.config['SECRET_KEY'] = secrets.token_urlsafe(12)
    app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:Qlammers3903@localhost/test_blog'
    token  = jwt.encode({
        'username': 'admin122',
        'exp': datetime.utcnow() + timedelta(hours=3),
            'user_login_status': True,
        },app.config['SECRET_KEY'],algorithm="HS256")
    db.drop_all()
    db.create_all()
    password = bcrypt.hashpw('123123'.encode('utf-8'),bcrypt.gensalt())
    test_user =User(username='admin122',email='testuser@gmail.com',password=password)
    another_test_user= User(username='admin123', email='testuser1@gmail.com',password=password)
    test_post = Post(title='something',body='something',timestamp=datetime.utcnow())
    test_user.posts.append(test_post)
    test_post2 = Post(title='something else',body='something else',timestamp=datetime.utcnow())
    test_user.posts.append(test_post2)
    test_post3= Post(title='something else',body='something else',timestamp=datetime.utcnow())
    test_post4= Post(title='something else',body='something else',timestamp=datetime.utcnow())
    test_user.posts.append(test_post3)
    another_test_user.posts.append(test_post4)
    db.session.add(test_user)
    db.session.add(another_test_user)
    db.session.add(test_post)
    db.session.add(test_post2)
    db.session.add(test_post3)
    db.session.add(test_post4)
    db.session.commit() 
    with app.test_client() as testing_client:
        with testing_client.session_transaction() as session:
            session['user_login_status'] = True
            session['token'] = token
        yield testing_client

def test_home_route(test_client):
    '''
    GIVEN one get request and one post request
    WHEN the home route is accessed
    THEN check for relavent status codes and response data
    '''
    response_get=test_client.get('/home')
    response_post=test_client.post('/home')
    assert response_post.status_code == 405
    assert response_get.status_code == 200
    assert b'<a class="create_post-btn" href="/posts/new">Create New Post</a>' not in response_get.data

def test_about_route(test_client):
    '''
    GIVEN one get request and one post request
    WHEN the about route is accessed
    THEN check for relavant status codes
    '''
    response_get= test_client.get('/about')
    response_post= test_client.post('/about')
    assert response_post.status_code == 405
    assert response_get.status_code == 200

def test_login_route(test_client):
    '''
    Given one get request and five post requests
    WHEN the login route is accessed
    THEN check for proper status codes, error messages and response data
    '''
    response_get= test_client.get('/login')
    response_post_null= test_client.post('/login')
    response_post_with_data=test_client.post('/login',data={
        'email':'testuser@gmail.com',
        'password': '123123'
    })
    response_post_with_invalid_email = test_client.post('/login',data={
        'email':'gibberish@gmail.com',
        'password': '123123'
    })
    response_post_with_invalid_password = test_client.post('/login',data={
        'email':'gibberish@gmail.com',
        'password': '123123'
    })
    response_post_with_empty_data = test_client.post('/login',data={
        'email':'',
        'password': ''
    })
    assert response_get.status_code == 200
    assert response_post_with_data.status_code == 302
    assert response_post_with_empty_data.status_code == 406
    assert b'Please complete all fields to login' in response_post_with_empty_data.data
    assert response_post_null.status_code == 406
    assert b'Please complete all fields to login' in response_post_null.data
    assert response_post_with_invalid_email.status_code == 401
    assert b'Username and password could not be verified' in response_post_with_invalid_email.data
    assert response_post_with_invalid_password.status_code == 401
    assert b'Username and password could not be verified' in response_post_with_invalid_password.data

def test_register_route(test_client):
    '''
    GIVEN one get request and seven post requests
    WHEN the register route is accessed
    THEN check for proper status codes, error messages and respose data
    '''
    response_get=test_client.get('/register')
    response_post_null=test_client.post('/register')
    response_post_empty_data= test_client.post('/register', data={
        'email':'',
        'username':'',
        'password1':'',
        'password2':'',
    })
    response_post_invalid_email= test_client.post('/register', data={
        'email':'invalid@email',
        'username':'test_user0',
        'password1':'123123',
        'password2':'123123',
    })
    response_post_passwords_not_matching = test_client.post('register', data={
        'email':'examplemail@email.com',
        'username':'test_user0',
        'password1':'123123',
        'password2':'1231234',
    })
    response_post_short_password = test_client.post('/register',data={
        'email':'examplemail@email.com',
        'username':'test_user0',
        'password1':'12312',
        'password2':'12312',
    })
    response_post_email_exists = test_client.post('/register', data={
        'email':'testuser@gmail.com',
        'username':'randomname',
        'password1':'123123',
        'password2':'123123',
    })
    response_post_username_exists= test_client.post('/register',data={
        'email':'testuse1@gmail.com',
        'username':'admin122',
        'password1':'123123',
        'password2':'123123',
    })
    assert response_get.status_code == 200
    assert response_post_null.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_null.data
    assert response_post_empty_data.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_empty_data.data
    assert response_post_invalid_email.status_code == 406
    assert b'Please enter a valid E-mail address' in response_post_invalid_email.data
    assert response_post_passwords_not_matching.status_code == 406
    assert b'The passwords must match' in response_post_passwords_not_matching.data
    assert response_post_short_password.status_code == 406
    assert b'The password must be at least six characters' in response_post_short_password.data
    assert response_post_email_exists.status_code == 406
    assert b'E-mail is already registered please sign in' in response_post_email_exists.data
    assert response_post_username_exists.status_code == 406 
    assert b'Username is already taken' in response_post_username_exists.data

def test_logout_route(test_client):
    '''
    GIVEN one get request and one post request
    WHEN the logout route is accessed
    THEN check for proper status codes
    '''
    response_get = test_client.get('/logout')
    response_post = test_client.post('/logout')
    assert response_get.status_code == 302
    assert response_post.status_code == 405

def test_create_post_route_unauth(test_client):
    '''
    GIVEN one post request and one get request
    WHEN a user who is not logged in tries to access the posts/new route
    THEN check for erros messages and unauthorized status codes and response data
    '''
    response_get = test_client.get('/posts/new')
    response_post = test_client.post('/posts/new')
    assert response_get.status_code == 401
    assert b'Stay up to date on the latest news with our handpicked recommendations ...' in response_get.data
    assert b'Stay up to date on the latest news with our handpicked recommendations ...' in response_post.data
    assert response_post.status_code == 401

def test_delete_post_route_unauth(test_client):
    '''
    GIVEN one post request and one get request
    WHEN a user who is not logged in tries to access the posts/<int:id>/delete route 
    THEN check for error messages and unauthorized status codes and and response data
    '''
    response_get= test_client.get('/posts/3/delete')
    response_post = test_client.post('/posts/3/delete')
    assert response_get.status_code == 401
    assert b'<h1>Login : </h1>\n    <form method="post">\n' in response_get.data
    assert response_post.status_code == 405

def test_update_post_route_unauth(test_client):
    '''
    GIVEN one post request and one get request
    WHEN a user who is not logged in tries to access the posts/<int:id>/edit route 
    THEN check for error messages and unauthorized status codes
    '''
    response_get=test_client.get('/posts/1/edit')
    response_post=test_client.post('/posts/1/edit')
    assert response_get.status_code == 401
    assert response_post.status_code == 401

def test_home_route_loggedin(test_loggedin_client):
    '''
    GIVEN one get request 
    WHEN a logged in user access's the home route 
    THEN check if the create post button is available for them and proper status code
    '''
    response_get = test_loggedin_client.get('/home')
    assert response_get.status_code == 200
    assert b'<a class="create_post-btn" href="/posts/new">Create New Post</a>' in response_get.data

def test_create_post_route_auth(test_loggedin_client):
    '''
    GIVEN one get request and and 3 post requests 
    WHEN a logged in user tries to create a new post via the posts/new route
    THEN check for proper status codes and error messages and response data for each request 
    '''
    response_get = test_loggedin_client.get('/posts/new')
    response_post_null_data = test_loggedin_client.post('/posts/new')
    response_post_empty_data = test_loggedin_client.post('/posts/new',data={
        'title':'',
        'body':''
    })
    response_post_valid_data = test_loggedin_client.post('/posts/new',data={
        'title':'anything',
        'body':'anything your heart desired'
    })
    assert response_get.status_code == 200
    assert b'<input type="text" name="title" placeholder="Title" />' in response_get.data
    assert response_post_null_data.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_null_data.data
    assert response_post_empty_data.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_empty_data.data
    assert response_post_valid_data.status_code == 302
    assert b'<a href="/home">/home</a>. If not, click the link.' in response_post_valid_data.data

def test_delete_post_route_auth(test_loggedin_client):
    '''
    GIVEN one post request and three get requests
    WHEN a logged in user tries to access the /posts/<int:id>/delete route 
    THEN check if the user has access to the route and other errors and status codes and response data
    '''
    response_post = test_loggedin_client.post('posts/3/delete')
    response_get_invalid_postid = test_loggedin_client.get('posts/300/delete')
    response_get_unrelated_user= test_loggedin_client.get('posts/4/delete')
    response_get_valid_delete = test_loggedin_client.get('posts/1/delete')
    assert response_post.status_code == 405
    assert response_get_invalid_postid.status_code == 404
    assert response_get_unrelated_user.status_code == 403
    assert response_get_valid_delete.status_code == 302
    assert b'<title>Redirecting...</title>' in response_get_valid_delete.data

def test_update_post_route_auth(test_loggedin_client):
    '''
    GIVEN one get request and five post request 
    WHEN  a logged in user tries to access the /posts/<int:id>/edit route
    THEN check if the user is authorized and check for error messages status codes and response data
    '''
    response_get=test_loggedin_client.get('/posts/2/edit')
    response_post_invalid_postid = test_loggedin_client.get('/posts/1000/edit')
    response_post_null_data = test_loggedin_client.post('/posts/2/edit')
    response_post_empty_data = test_loggedin_client.post('/posts/2/edit', data={
        'title':'',
        'body':''
    })
    response_post_unrelated_user = test_loggedin_client.post('/posts/4/edit', data={
        'title':'boo',
        'body':'foo'
    })
    response_post_valid_user_data = test_loggedin_client.post('/posts/2/edit', data={
        'title':'boo',
        'body':'foo'
    })
    assert response_get.status_code == 200
    assert response_post_invalid_postid.status_code == 404
    assert b'Post could not be found' in response_post_invalid_postid.data
    assert response_post_null_data.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_null_data.data
    assert response_post_empty_data.status_code == 406
    assert b'Please do not leave any fields blank' in response_post_empty_data.data
    assert response_post_unrelated_user.status_code == 403
    assert b'<h1>Login : </h1>' in response_post_unrelated_user.data
    assert response_post_valid_user_data.status_code == 302
    assert b'<a href="/home">/home</a>. If not, click the link.\n' in response_post_valid_user_data.data

def test_db_for_new_user(test_client): 
    '''
    GIVEN a post request to register a new user
    WHEN  a user tries to register without any errors
    THEN check if the database has stored the new user 
    '''
    test_client.post('/register', data={
        'email':'testuser12@gmail.com',
        'username':'admin124',
        'password1':'123123',
        'password2':'123123',
    })
    query_user =db.session.query(User).filter_by(username='admin124')
    assert query_user.count() == 1
    query_user = query_user.first()
    assert query_user.email == 'testuser12@gmail.com'
    assert query_user.password != '123123'

def test_db_for_new_post(test_loggedin_client):
    '''
    GIVEN a post request to make a new post 
    WHEN a user is logged in and tries to create a new post without any erros
    THEN check if the new post has been stored in the database
    '''
    test_loggedin_client.post('/posts/new', data={
        'title': 'The bernstien brothers',
        'body': 'They suck'
    })
    query_post=db.session.query(Post).filter_by(title='The bernstien brothers')
    assert query_post is not None
    query_post= query_post.first()
    assert query_post.user.username == 'admin122'
    assert query_post.body == 'They suck'

def test_db_for_deleted_post(test_loggedin_client):
    '''
    GIVEN a get request to delete a post
    WHEN  an authorized user tries to delete their posts
    THEN check the database to ensure the data was deleted 
    '''
    test_loggedin_client.get('posts/3/delete')
    query_deletedpost = db.session.query(Post).get(3)
    assert query_deletedpost == None

def test_db_for_updated_post(test_loggedin_client):
    '''
    GIVEN a post request to update a post
    WHEN  an authorized user tries to update one of thier posts
    THEN check if the data for the post gets updated in the database
    '''
    test_loggedin_client.post('/posts/2/edit', data={
        'title':'Bobby brown',
        'body': 'Uncle thomas'
    })
    query_updated_post= db.session.query(Post).get(2)
    assert query_updated_post.title == 'Bobby brown'
    assert query_updated_post.body == 'Uncle thomas'

def test_admin_login(test_loggedin_client):
    '''
    GIVEN a post request to the login route
    WHEN the user trying to login is an admin with proper credentials 
    THEN check to see if the user is routed to the proper admin page and response data matches expectations 
    '''
    password = password = bcrypt.hashpw('123123'.encode('utf-8'),bcrypt.gensalt())
    admin=User(username='admin',email='adminuser@email.com',password=password,admin_status=True)
    db.session.add(admin)
    db.session.commit()
    response = test_loggedin_client.post('login',data={
        'email':'adminuser@email.com',
        'password': '123123'
    })
    assert response.status_code == 302
    assert b'<div class="admin-container">' in response.data