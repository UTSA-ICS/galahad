import	dataset
import	json

db = dataset.connect('sqlite:///mydatabase.db')
table = db['user']

d = {
	'name':'John Doe',
	'age':'46',
	'country':'China',
}

parsed_json = json.loads(json.dumps(d))

print(json.dumps(d))
print(parsed_json)

table.insert(parsed_json)

#table.insert(dict(name:'John Doe', age:46, country:'China'))
#table.insert(dict(name='Jane Doe', age=37, country='France', gender='female'))

#table.update(dict(name='Jane Doe', age=47), ['name'])

print(db.tables)

table.drop()
