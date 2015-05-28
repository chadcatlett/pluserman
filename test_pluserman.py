import json
import os
import tempfile
import unittest

import pluserman


class PLUserManagerTestCase(unittest.TestCase):

    def clean_db_slate(self):
        pluserman.init_db()

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, pluserman.app.config['DATABASE'] = tempfile.mkstemp()
        pluserman.app.config['TESTING'] = True
        self.app = pluserman.app.test_client()
        self.clean_db_slate()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(pluserman.app.config['DATABASE'])

    def test_index(self):
        rv = self.app.get("/")
        self.assertEqual(rv.data, 'Hi.')


class GroupTestCase(unittest.TestCase):

    def clean_db_slate(self):
        pluserman.init_db()

    def get_group_members(self, group_name):
        rv = self.app.get("/groups/%s" % (group_name,))
        return json.loads(rv.data)

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, pluserman.app.config['DATABASE'] = tempfile.mkstemp()
        pluserman.app.config['TESTING'] = True
        self.app = pluserman.app.test_client()
        self.clean_db_slate()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(pluserman.app.config['DATABASE'])

    def test_group_listing(self):
        self.clean_db_slate()
        expected_groups = [
            "wheel",
            "users",
            "restricted"
        ]
        expected_groups.sort()

        rv = self.app.get("/groups")
        result_groups = json.loads(rv.data)
        result_groups.sort()

        self.assertListEqual(expected_groups, result_groups)

    def test_group_member_listing(self):
        self.clean_db_slate()
        expected_groups = {
            'wheel': [
                'admin',
            ],
            'users': [
                'admin',
                'user1',
            ],
            'restricted': [
                'user1',
            ]
        }

        for expected_group, expected_members in expected_groups.iteritems():
            result_members = self.get_group_members(expected_group)
            result_members.sort()
            self.assertListEqual(expected_members, result_members)

    def test_group_404(self):
        self.clean_db_slate()
        rv = self.app.get("/group/asdfasdfasdfasdfadfasdfadfasdfasdfasdf")
        self.assertEqual(rv.status_code, 404)

    def test_group_delete(self):
        self.clean_db_slate()

        rv = self.app.delete("/groups/wheel")
        self.assertEqual(rv.status_code, 204)

        rv = self.app.get("/users/admin")
        self.assertEqual(rv.status_code, 200)

        user_record = json.loads(rv.data)
        self.assertNotIn("wheel", user_record['groups'])

    def test_group_creation(self):
        self.clean_db_slate()
        rv = self.app.get("/group/newgroup")
        self.assertEqual(rv.status_code, 404)

        rv = self.app.post("/groups", data=dict(name="newgroup"))
        self.assertEqual(rv.status_code, 201)

        rv = self.app.get("/groups")
        groups = json.loads(rv.data)

        self.assertIn("newgroup", groups)

        rv = self.app.get("/groups/newgroup")
        new_group = json.loads(rv.data)

        self.assertEqual(len(new_group), 0)

    def test_group_creation_duplicate(self):
        self.clean_db_slate()
        rv = self.app.get("/group/wheel")
        self.assertEqual(rv.status_code, 404)

        rv = self.app.post("/groups", data=dict(name="wheel"))
        self.assertEqual(rv.status_code, 409)

    def test_group_put_test_valid_users(self):
        self.clean_db_slate()

        original_users = self.get_group_members("users")

        new_users = list(original_users)
        new_users.append("lonely")
        new_users.sort()

        rv = self.app.put("/groups/users", data=json.dumps(new_users))
        self.assertEquals(rv.status_code, 200)

        updated_users = self.get_group_members("users")
        updated_users.sort()

        self.assertListEqual(new_users, updated_users)

    def test_group_put_test_invalid_users(self):
        self.clean_db_slate()

        original_users = self.get_group_members("users")

        new_users = list(original_users)
        new_users.append("notfounduser")
        new_users.sort()

        rv = self.app.put("/groups/users", data=json.dumps(new_users))
        self.assertEquals(rv.status_code, 422)

    def test_group_put_test_empty_group(self):
        self.clean_db_slate()
        original_users = self.get_group_members("users")
        new_users = []
        rv = self.app.put("/groups/users", data=json.dumps(new_users))
        self.assertEquals(rv.status_code, 200)

        current_users = self.get_group_members("users")
        self.assertListEqual(new_users, current_users)


class UserTestCase(unittest.TestCase):

    def clean_db_slate(self):
        pluserman.init_db()

    def setUp(self):
        """Before each test, set up a blank database"""
        self.db_fd, pluserman.app.config['DATABASE'] = tempfile.mkstemp()
        pluserman.app.config['TESTING'] = True
        self.app = pluserman.app.test_client()
        self.clean_db_slate()

    def tearDown(self):
        """Get rid of the database again after each test."""
        os.close(self.db_fd)
        os.unlink(pluserman.app.config['DATABASE'])

    def test_user_index_listing(self):
        expected_users = [
            'admin',
            'lonely',
            'user1',
        ]
        expected_users.sort()

        rv = self.app.get('/users')
        result_users = json.loads(rv.data)
        result_users.sort()

        self.assertListEqual(expected_users, result_users)

    def test_user_does_404(self):
        rv = self.app.get("/users/asdfasdfadsfadsfadsfadsfadsfadf")
        self.assertEqual(rv.status_code, 404)

    def test_user_get(self):
        expected_user = {
            'userid': 'admin',
            'first_name': 'Mighty',
            'last_name': 'Admin',
            'groups': [
                'users',
                'wheel'
            ]
        }
        rv = self.app.get("/users/admin")
        self.assertEqual(rv.status_code, 200)
        result_user = json.loads(rv.data)
        result_user['groups'].sort()
        self.assertDictEqual(expected_user, result_user)


    def test_user_create_conficts(self):
        self.clean_db_slate()

        new_user = {
            'userid': 'admin',
            'first_name': 'Newb',
            'last_name': 'ie',
            'groups': [
                'users',
                'wheel'
            ]
        }

        rv = self.app.post("/users", data=json.dumps(new_user))

        self.assertEqual(rv.status_code, 409)

    def test_user_create_bad_data(self):
            self.clean_db_slate()

            new_user = {
                'test':'fail'
            }

            rv = self.app.post("/users", data=json.dumps(new_user))

            self.assertEqual(rv.status_code, 400)


    def test_user_create_with_groups(self):
        self.clean_db_slate()

        new_user = {
            'userid': 'newbie',
            'first_name': 'Newb',
            'last_name': 'ie',
            'groups': [
                'users',
                'wheel'
            ]
        }

        rv = self.app.post("/users", data=json.dumps(new_user))

        self.assertEqual(rv.status_code, 201)

        rv = self.app.get("/users/newbie")
        self.assertEqual(rv.status_code, 200)

        user_record = json.loads(rv.data)
        user_record['groups'].sort()

        self.assertDictEqual(new_user, user_record)

    def test_user_create_with_invalid_groups(self):
        self.clean_db_slate()

        new_user = {
            'userid': 'newbie',
            'first_name': 'Newb',
            'last_name': 'ie',
            'groups': [
                'sysadmins',
                'executives',
                'wheel'
            ]
        }

        rv = self.app.post("/users", data=json.dumps(new_user))
        self.assertEqual(rv.status_code, 400)

    def test_user_create_without_groups(self):
        self.clean_db_slate()

        new_user = {
            'userid': 'newbie',
            'first_name': 'Newb',
            'last_name': 'ie',
            'groups': [],
        }

        rv = self.app.post("/users", data=json.dumps(new_user))

        self.assertEqual(rv.status_code, 201)

        rv = self.app.get("/users/newbie")
        self.assertEqual(rv.status_code, 200)

        user_record = json.loads(rv.data)
        user_record['groups'].sort()

        self.assertDictEqual(new_user, user_record)

    def test_user_delete(self):
        rv = self.app.delete("/users/admin")
        self.assertEqual(rv.status_code, 204)

        rv = self.app.get("/users/admin")
        self.assertEqual(rv.status_code, 404)

        rv = self.app.get("/groups/wheel")

        wheel_members = json.loads(rv.data)

        self.assertNotIn('admin',wheel_members)


if __name__ == "__main__":
    unittest.main()
