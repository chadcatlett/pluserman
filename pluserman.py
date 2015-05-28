# boiler plate portions shamelessly taken from flask's examples.


from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request,  abort, _app_ctx_stack

from utils import *

DATABASE = '/tmp/pluserman.db'
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('PLUSERMAN_SETTINGS', silent=True)

HTTP_CODE_OK = 200
HTTP_CODE_CREATED = 201
HTTP_CODE_DELETED = 204 # technically No Content, often used for deletion messages
HTTP_CODE_CLIENT_BAD_REQUEST = 400
HTTP_CODE_NOT_FOUND = 404
HTTP_CODE_CONFLICT = 409
HTTP_CODE_UNPROCESSABLE_ENTITY = 422
HTTP_CODE_SERVER_GENERIC_ERROR = 500
HTTP_CODE_SERVER_NOT_IMPLEMENTED = 501

def get_db():
    top = _app_ctx_stack.top
    if not hasattr(top, 'sqlite_db'):
        sqlite_db = sqlite3.connect(app.config['DATABASE'])
        sqlite_db.execute("PRAGMA foreign_keys=on")
        sqlite_db.row_factory = sqlite3_dict_factory
        top.sqlite_db = sqlite_db
    return top.sqlite_db


def init_db():
    """Creates the database tables."""
    with app.app_context():
        db = get_db()
        with app.open_resource('main.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.teardown_appcontext
def close_db_connection(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'sqlite_db'):
        top.sqlite_db.close()

@app.route('/')
def index():
    return "Hi."


@app.route('/users', methods=['GET', 'POST'])
def user_index():
    db = get_db()
    if request.method == 'GET':
        return json_response(user_list(db))

    elif request.method == 'POST':
        user_data = request.get_json(force=True)
        if user_data is None:
            abort(HTTP_CODE_CLIENT_BAD_REQUEST)

        if not validate_user_dict(db, user_data):
            abort(HTTP_CODE_CLIENT_BAD_REQUEST)

        if user_exists(db, user_data['userid']):
            abort(HTTP_CODE_CONFLICT)

        if user_create(db, user_data):
            return '', HTTP_CODE_CREATED
        abort(HTTP_CODE_SERVER_GENERIC_ERROR)
    abort(HTTP_CODE_SERVER_NOT_IMPLEMENTED)


@app.route('/users/<userid>', methods=['DELETE', 'GET', 'PUT'])
def user_handler_entry(userid):
    db = get_db()

    if not user_exists(db, userid):
        abort(HTTP_CODE_NOT_FOUND)

    if request.method == 'GET':
        return json_response(user_details(db, userid))

    elif request.method == 'DELETE':
        if user_delete(db, userid):
            return '', HTTP_CODE_DELETED
        abort(HTTP_CODE_SERVER_GENERIC_ERROR)

    elif request.method == 'PUT':
        abort(HTTP_CODE_SERVER_NOT_IMPLEMENTED)
    abort(HTTP_CODE_SERVER_NOT_IMPLEMENTED)

@app.route('/groups', methods=['GET', 'POST'])
def group_index():
    db = get_db()

    if request.method == 'GET':
        return json_response(group_list(db))

    elif request.method == 'POST':
        if not request.form['name']:
            abort(HTTP_CODE_CLIENT_BAD_REQUEST)

        group_name = request.form['name']
        if group_exists(db, group_name):
            abort(HTTP_CODE_CONFLICT)

        if group_create(db, group_name):
            return '', HTTP_CODE_CREATED
        abort(HTTP_CODE_SERVER_GENERIC_ERROR)

    abort(HTTP_CODE_SERVER_NOT_IMPLEMENTED)


@app.route('/groups/<group_name>', methods=['DELETE', 'GET', 'PUT'])
def group_handler_entry(group_name):
    db = get_db()

    if not group_exists(db, group_name):
        abort(HTTP_CODE_NOT_FOUND)

    if request.method == 'GET':
        return json_response(group_get_members(db, group_name))

    elif request.method == 'PUT':
        group_members = request.get_json(force=True)
        if group_set_members(db, group_name, group_members):
            return '', HTTP_CODE_OK
        abort(HTTP_CODE_UNPROCESSABLE_ENTITY)

    elif request.method == 'DELETE':
        if group_delete(db, group_name):
            return '', HTTP_CODE_DELETED
        abort(HTTP_CODE_SERVER_GENERIC_ERROR)

    abort(HTTP_CODE_SERVER_NOT_IMPLEMENTED)

if __name__ == '__main__':
    app.run()
