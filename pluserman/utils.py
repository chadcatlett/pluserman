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


class DB(object):

    def __init__(self, db_connection):
        self.connection = db_connection

    def group_list(self):
        cursor = self.connection.execute("SELECT name FROM [group]")
        return [i['name'] for i in cursor]

    def group_exists(self, group_name):
        cursor = self.connection.execute("SELECT name FROM [group] WHERE name=?", (group_name,))
        results = cursor.fetchone()
        return True if results else False

    def group_get_members(self, group_name):
        cursor = self.connection.execute("SELECT userid FROM [group] JOIN group_membership ON [group].id=group_membership.group_id JOIN user ON group_membership.user_id=user.id WHERE name=?", (group_name,))
        return [i['userid'] for i in cursor]

    def group_set_members(self, group_name, members):
        if not self.group_exists(group_name):
            return False

        for member in members:
            if not self.user_exists(member):
                return False

        cursor = self.connection.execute("SELECT id FROM [group] WHERE name=?", (group_name,))
        group_id = cursor.fetchone()['id']
        user_ids = []

        # terrible way todo this, but I couldn't sanely figure out how to use an IN() query with sqlite3
        # to make this section better.

        cursor = self.connection.execute("DELETE FROM group_membership WHERE group_id=?", (group_id,))
        self.connection.commit()

        if not members:
            return True

        for member in members:
            cursor = self.connection.execute("SELECT id FROM user WHERE userid=?", (member,))
            user_id = cursor.fetchone()['id']
            user_ids.append(user_id)

        self.connection.executemany("INSERT INTO group_membership (group_id, user_id) VALUES(? ,?)", zip(repeat(group_id), user_ids))
        self.connection.commit()
        return True

    def group_add_member(self, group_name, member):
        members = self.group_get_members(group_name)
        members.append(member)
        return self.group_set_members(group_name, members)

    def group_create(self, group_name):
        if self.group_exists(group_name):
            return False
        cursor = self.connection.execute("INSERT INTO [group] (name) VALUES (?)", (group_name,))
        self.connection.commit()
        return cursor.rowcount

    def group_delete(self, group_name):
        if not self.group_exists(group_name):
            return False
        cursor = self.connection.execute("DELETE FROM [group] WHERE name=?", (group_name,))
        self.connection.commit()
        return cursor.rowcount

    def user_list(self):
        cursor = self.connection.execute("SELECT userid FROM user")
        return [i['userid'] for i in cursor]

    def user_exists(self, userid):
        cursor = self.connection.execute("SELECT userid FROM user WHERE userid=?", (userid,))
        results = cursor.fetchone()
        return True if results else False

    def user_delete(self, userid):
        if not self.user_exists(userid):
            return False
        cursor = self.connection.execute("DELETE FROM user WHERE userid=?", (userid,))
        self.connection.commit()
        return cursor.rowcount

    def user_details(self, userid):

        if not self.user_exists(userid):
            return None

        user_dict = dict()
        user_dict['userid'] = userid
        user_dict['groups'] = []

        cursor = self.connection.execute("SELECT userid, first_name, last_name, [group].name as group_name FROM user LEFT OUTER JOIN group_membership ON user.id=group_membership.user_id LEFT OUTER JOIN [group] on group_membership.group_id=[group].id WHERE userid=?", (userid,))

        for i in cursor:
            user_dict['first_name'] = i['first_name']
            user_dict['last_name'] = i['last_name']
            if i['group_name']:
                user_dict['groups'].append(i['group_name'])

        return user_dict

    def user_create(self, user_data):

        if self.user_exists(user_data['userid']):
            return False
        userid = user_data['userid']
        first_name = user_data['first_name']
        last_name = user_data['last_name']

        cursor = self.connection.execute("INSERT INTO user (userid, first_name, last_name) VALUES(?,?,?)",(userid, first_name, last_name))
        self.connection.commit()

        for group in user_data['groups']:
            self.group_add_member(group, userid)
        return True

    def validate_user_dict(self, user):
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
            if not self.group_exists(i):
                return False

        return True
