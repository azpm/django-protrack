import informixdb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PROTRACK_USER = ""
PROTRACK_PASSWORD = ""

def connect():
    return informixdb.connect('protrack@ptrack_odbc', user=PROTRACK_USER, password=PROTRACK_PASSWORD)

def _fluck_protrack(*args, **kwargs):
    raise NotImplementedError()

#we have to override the this because our informix doesn't support transactions or roles
protrack_engine = create_engine('informix://', creator=connect, has_transactions = False)
protrack_engine.dialect._get_default_schema_name = _fluck_protrack # this wasn't originally called fluck

Session = sessionmaker(bind = protrack_engine)