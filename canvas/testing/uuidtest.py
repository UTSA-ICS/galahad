import uuid, re
sid = str(uuid.uuid4())
sid = re.sub("[^0-9]","",sid)
print(sid[:10])
