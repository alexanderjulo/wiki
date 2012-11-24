import os
import json

class UserManager(object):
	"""A very simple user Manager, that saves it's data as json."""
	def __init__(self, path):
		self.file = os.path.join(path, 'users.json')

	def read(self):
		if not os.path.exists(self.file):
			return {}
		with open(self.file) as f:
			data = json.loads(f.read())
		return data

	def write(self, data):
		with open(self.file, 'w') as f:
			f.write(json.dumps(data, indent=2))

	def add_user(self, name, password, active=True, roles=[]):
		users = self.read()
		if users.get(name):
			return False
		users[name] = {
			'password': password,
			'active': active,
			'roles': roles,
			'authenticated': False
		}
		self.write(users)
		userdata = users.get(name)
		return User(self, name, userdata)

	def get_user(self, name):
		users = self.read()
		userdata = users.get(name)
		if not userdata:
			return None
		return User(self, name, userdata)

	def delete_user(self, name):
		users = self.read()
		if not self.pop(name):
			return False
		self.write(users)
		return True

	def update(self, name, userdata):
		data = self.read()
		data[name] = userdata
		self.write(data)

class User(object):
	
	def __init__(self, manager, name, data):
		self.manager = manager
		self.name = name
		self.data = data

	def get(self, option):
		return self.data.get(option)

	def set(self, option, value):
		self.data[option] = value
		self.save()

	def save(self):
		self.manager.update(self.name, self.data)

	def is_authenticated(self):
		return self.data.get('authenticated')

	def is_active(self):
		return self.data.get('active')

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.name
