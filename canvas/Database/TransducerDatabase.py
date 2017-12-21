import	dataset
import	time
import	datetime

class TransducerDatabase:
	def __init__(self):
		self._transducerId = None
		self._name = None
		self._type = None
		self._startEnabled = None
		self._startingConfig = None
		self._requiredAccess = None
		self._userToken = None
		self._db = dataset.connect('sqlite:////home/kelli/galahad/canvas/Database/canvas.db')
		self._table = self._db['TRANSDUCER']

	def set_user(self, userToken):
		self._userToken = userToken

	def set_values(self, values_json):
		self._transducerId = values_json['TRANSID']			# create
		self._name = values_json['NAME']
		self._type = values_json['TYPE']
		self._startEnabled = values_json['STARTENABLED']
		self._startingConfig = values_json['STARTCONFIG']
		self._requiredAccess = values_json['REQACCESS']

	def insert(self):
		d = {
			'TRANSID'					: self._transducerId,
			'NAME'						: self._name,
			'TYPE'						: self._type,
			'STARTENABLED'				: self._startEnabled,
			'STARTCONFIG'				: self._startingConfig,
			'REQACCESS'					: self._requiredAccess,
			'USERTOKEN'					: self._userToken,
		}
		self._table.upsert(d,['TRANSID'])
		return self._transducerId

	def find_one(self, transducerId):
		return self._table.find_one(USERTOKEN=self._userToken,
									TRANSID=transducerId)

	def find_all(self):
		transducers = []
		data = self._table.all()
		for transducer in data:
			transducers.append(transducer)
		return transducers

if __name__ == '__main__':
	trans = TransducerDatabase()
	trans.set_user('kelli')
	trans.set_values({
		'TRANSID'						: 'temp',
		'NAME'							: 'name',
		'TYPE'							: 'SENSOR',
		'STARTENABLED'					: True,
		'STARTCONFIG'					: '',
		'REQACCESS'						: '[NETWORK]',
	})
	transid = trans.insert()
	print trans.find_one(transid)
	print trans.find_all()
