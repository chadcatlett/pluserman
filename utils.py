import json
from itertools import repeat
from flask import current_app


def sqlite3_dict_factory(cursor, row):
    """
        Factory function that creates a dict that also fakes a list/tuple result
        by adding numeric keys for indexing. It of course has limitations. Beware.
    """
    dict_row = dict()
    for idx, col in enumerate(cursor.description):
        dict_row[col[0]] = row[idx]
        dict_row[idx] = row[idx]
    return dict_row


def json_response(data):
    """
    Since the requirements dictated the ability to return lists
    for /groups/<group name>, this was used instead of the default jsonify from Flask
    """
    return current_app.response_class(
        json.dumps(data),
        mimetype="application/json"
    )


def group_list(db):
    cursor = db.execute("SELECT name FROM [group]")
    return [i['name'] for i in cursor]

def group_exists(db, group_name):
    cursor = db.execute("SELECT name FROM [group] WHERE name=?", (group_name,))
    results = cursor.fetchone()
    return True if results else False

def group_get_members(db, group_name):
    cursor = db.execute("SELECT userid FROM [group] JOIN group_membership ON [group].id=group_membership.group_id JOIN user ON group_membership.user_id=user.id WHERE name=?", (group_name,))
    return [i['userid'] for i in cursor]

def group_set_members(db, group_name, members):
    if not group_exists(db, group_name):
        return False

    for member in members:
        if not user_exists(db, member):
            return False

    cursor = db.execute("SELECT id FROM [group] WHERE name=?", (group_name,))
    group_id = cursor.fetchone()['id']
    user_ids = []

    # terrible way todo this, but I couldn't sanely figure out how to use an IN() query with sqlite3
    # to make this section better.

    cursor = db.execute("DELETE FROM group_membership WHERE group_id=?", (group_id,))
    db.commit()

    if not members:
        return True

    for member in members:
        cursor = db.execute("SELECT id FROM user WHERE userid=?", (member,))
        user_id = cursor.fetchone()['id']
        user_ids.append(user_id)

    db.executemany("INSERT INTO group_membership (group_id, user_id) VALUES(? ,?)", zip(repeat(group_id), user_ids))
    db.commit()
    return True

def group_add_member(db, group_name, member):
    members = group_get_members(db, group_name)
    members.append(member)
    return group_set_members(db, group_name, members)

def group_create(db, group_name):
    if group_exists(db, group_name):
        return False
    cursor = db.execute("INSERT INTO [group] (name) VALUES (?)", (group_name,))
    db.commit()
    return cursor.rowcount

def group_delete(db, group_name):
    if not group_exists(db, group_name):
        return False
    cursor = db.execute("DELETE FROM [group] WHERE name=?", (group_name,))
    db.commit()
    return cursor.rowcount

def user_list(db):
    cursor = db.execute("SELECT userid FROM user")
    return [i['userid'] for i in cursor]


def user_exists(db, userid):
    cursor = db.execute("SELECT userid FROM user WHERE userid=?", (userid,))
    results = cursor.fetchone()
    return True if results else False


def user_delete(db, userid):
    if not user_exists(db, userid):
        return False
    cursor = db.execute("DELETE FROM user WHERE userid=?", (userid,))
    db.commit()
    return cursor.rowcount


def user_details(db, userid):

    if not user_exists(db, userid):
        return None

    user_dict = dict()
    user_dict['userid'] = userid
    user_dict['groups'] = []

    cursor = db.execute("SELECT userid, first_name, last_name, [group].name as group_name FROM user LEFT OUTER JOIN group_membership ON user.id=group_membership.user_id LEFT OUTER JOIN [group] on group_membership.group_id=[group].id WHERE userid=?", (userid,))

    for i in cursor:
        user_dict['first_name'] = i['first_name']
        user_dict['last_name'] = i['last_name']
        if i['group_name']:
            user_dict['groups'].append(i['group_name'])

    return user_dict

def user_create(db, user_data):

    if user_exists(db, user_data['userid']):
        return False
    userid = user_data['userid']
    first_name = user_data['first_name']
    last_name = user_data['last_name']

    cursor = db.execute("INSERT INTO user (userid, first_name, last_name) VALUES(?,?,?)",(userid, first_name, last_name))
    db.commit()

    for group in user_data['groups']:
        group_add_member(db, group, userid)
    return True


def validate_user_dict(db, user):
    if not isinstance(user, dict):
        return False

    VALID_STRINGS = (unicode, str)
    required_keys = {
        'userid': VALID_STRINGS,
        'first_name': VALID_STRINGS,
        'last_name': VALID_STRINGS,
        'groups': (list,)
    }

    for key, valid_types in required_keys.iteritems():
        if key not in user or not isinstance(user[key], valid_types):
            return False

    for i in user['groups']:
        if not isinstance(i, VALID_STRINGS):
            return False
        if not group_exists(db, i):
            return False

    return True