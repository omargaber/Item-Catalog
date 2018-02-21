from flask import Flask, render_template
from flask import request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Items, User

from flask import session as login_session
from flask import session as cross_pages_login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

authentication_dict = {}

engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


# @app.route('/login')
# def showLogin():
#     state = ''.join(random.choice(string.ascii_uppercase + string.digits)
#                     for x in xrange(32))
#     login_session['state'] = state
#     return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'),
            200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

    # DISCONNECT - Revoke a current user's token and reset their login_session


# Used to create user and stored in Users table on login
def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    creted_user_id = session.query(User).filter_by(
        email=login_session['email']).one()
    return creted_user_id.id


# Returns object of type User
def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Returns user id if email existed in users table
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']        # NOQA
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        return redirect(url_for('categoryList'))
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Landing page of the app
@app.route('/')
def categoryList():
    # Checks if there is a logged-in user currently
    if 'username' in login_session:
        categories = session.query(Category).all()
        recent_items = session.query(Items).order_by(Items.id.desc()).limit(7)
        return render_template(
            'loggedinmain.html',
            categoryList=categories,
            latest=recent_items,
            STATE=login_session['state'])
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        cross_pages_login_session['state'] = state
        categories = session.query(Category).all()
        recent_items = session.query(Items).order_by(Items.id.desc()).limit(7)
        return render_template(
            'main.html',
            categoryList=categories,
            latest=recent_items,
            STATE=state)


# Creates JSON endpoint
@app.route('/catalog')
@app.route('/catalog.json')
def jsonEndpoint():
    if request.method == 'GET':
        cat = []
        itemPerCat = []
        categories = session.query(Category).all()
        for categ in categories:
            cat.append(categ.serialize)
            items = session.query(Items).filter_by(category_id=categ.id).all()
            for ite in items:
                itemPerCat.append(ite.serialize)

        return jsonify({'Category': cat, 'Items':  itemPerCat})


# Loads items and item count of a category
@app.route('/catalog/<category>/items/', methods=['GET'])
def categoryItems(category):
    # Checks if there is a logged-in user currently
    if 'username' in login_session:
        categories = session.query(Category).all()
        category_chosen = session.query(
            Category).filter_by(name=category).one()
        items_of_category = session.query(Items).filter_by(
            category_id=category_chosen.id)
        return render_template(
            'loggedincategoryitems.html',
            categoryList=categories,
            categor=category_chosen,
            id=items_of_category,
            itemCount=items_of_category.count(),
            STATE=login_session['state'])
    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        # cross_pages_login_session['state'] = state
        categories = session.query(Category).all()
        category_chosen = session.query(
            Category).filter_by(name=category).one()
        items_of_category = session.query(Items).filter_by(
            category_id=category_chosen.id)
        return render_template(
            'categoryitems.html',
            categoryList=categories,
            categor=category_chosen,
            id=items_of_category,
            itemCount=items_of_category.count(),
            STATE=state)


# Loads item name and its description
@app.route('/catalog/<category>/<int:item>/')
def getItemDescription(category, item):
    itemString = session.query(Items).filter_by(id=item).one()
    # CHecks if there is a logged-in user currently
    if 'username' in login_session:
        item_user_id = session.query(Items).filter_by(
            name=itemString.name).one()
        creator = getUserInfo(item_user_id.user_id)
        item_chosen = session.query(Items).filter_by(
            name=itemString.name).one()
        if login_session['username'] == creator.name:
            return render_template(
                'loggedinitemdescription.html',
                item_browsed=item_chosen,
                STATE=login_session['state'])
        elif login_session['username'] != creator.name:
            return render_template(
                'loggedinpublicitemdescription.html',
                item_browsed=item_chosen,
                STATE=login_session['state'])

    else:
        state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for x in xrange(32))
        login_session['state'] = state
        item_chosen = session.query(Items).filter_by(id=item).one()
        return render_template(
            'itemdescription.html',
            item_browsed=item_chosen,
            STATE=state)


# Creates new item by the currently logged-in user
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    else:
        if request.method == 'POST':
            categories = session.query(Category).all()
            recent_items = session.query(
                Items).order_by(Items.id.desc()).limit(7)

            cat = session.query(Category).filter_by(
                name=request.form.get('selected')).one()
            item_name = request.form['name']
            item_description = request.form['description']
            newItem = Items(name=item_name, description=item_description,
                            category=cat, user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            return render_template(
                'loggedinmain.html',
                categoryList=categories,
                latest=recent_items,
                STATE=login_session['state'])
        else:
            categories = categories = session.query(Category).all()
            return render_template(
                'newitem.html',
                categoryList=categories,
                STATE=login_session['state'])


# Allows authorized users edit the items they created &
# only view the items they didn't
@app.route("/catalog/<int:item>/edit", methods=['GET', 'POST'])
def editItem(item):
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    else:
        itemString = session.query(Items).filter_by(id=item).one()
        if request.method == 'POST':
            item_user_id = session.query(Items).filter_by(
                name=itemString.name).one()
            creator = getUserInfo(item_user_id.user_id)
            item_chosen = session.query(Items).filter_by(
                name=itemString.name).one()

            if login_session['username'] == creator.name:
                chosen_item = session.query(Items).filter_by(
                    name=itemString.name).one()
                chosen_item.name = request.form['name']
                chosen_item.description = request.form['description']
                session.add(chosen_item)
                session.commit()
                return redirect(url_for(
                    'getItemDescription',
                    category=chosen_item.category.name,
                    item=chosen_item.id))

            elif login_session['username'] == creator.name:
                script = "<script> function foo() {alert"
                script += "('You are not authorized to edit this item.');}"
                script += "</script><body onload='foo()'>"
                return script

        else:
            if 'username' in login_session:

                item_user_id = session.query(Items).filter_by(
                    name=itemString.name).one()
                creator = getUserInfo(item_user_id.user_id)
                item_chosen = session.query(Items).filter_by(
                    name=itemString.name).one()

                if login_session['username'] == creator.name:
                    categories = categories = session.query(Category).all()
                    chosen_name = session.query(Items).filter_by(
                        name=itemString.name).one()
                    return render_template(
                        'edititem.html',
                        item_edit=chosen_name,
                        categoryList=categories,
                        STATE=login_session['state'])

                elif login_session['username'] != creator.name:
                    script = "<script> function foo() {alert"
                    script += "('You are not authorized to edit this item.');}"
                    script += "</script><body onload='foo()'>"
                    return script

            else:
                return redirect(url_for('categoryList'))


# Allows authorized users to delete the items they created &
# restricts any other users from doing so
@app.route("/catalog/<int:item>/delete", methods=['GET', 'POST'])
def deleteItem(item):
    if 'username' not in login_session:
        return redirect(url_for('categoryList'))
    else:
        itemString = session.query(Items).filter_by(id=item).one()

        if request.method == 'POST':
            item_user_id = session.query(Items).filter_by(
                name=itemString.name).one()
            creator = getUserInfo(item_user_id.user_id)
            item_chosen = session.query(Items).filter_by(
                name=itemString.name).one()

            if login_session['username'] == creator.name:
                chosen_item = session.query(Items).filter_by(
                    name=itemString.name).one()
                session.delete(chosen_item)
                session.commit()
                return redirect(url_for('categoryList'))
            elif login_session['username'] != creator.name:
                script = "<script> function foo() {alert"
                script += "('You are not authorized to delete this item.');}"
                script += "</script><body onload='foo()'>"
                return script

        else:
            if 'username' in login_session:

                item_user_id = session.query(Items).filter_by(
                    name=itemString.name).one()
                creator = getUserInfo(item_user_id.user_id)
                item_chosen = session.query(Items).filter_by(
                    name=itemString.name).one()

                if login_session['username'] == creator.name:
                    return render_template('deleteitem.html')

                elif login_session['username'] != creator.name:
                    script = "<script> function foo() {alert"
                    script += "('You are not authorized to delete this item.')"
                    script += ";}</script><body onload='foo()'>"
                    return script

            else:
                return redirect(url_for('categoryList'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
