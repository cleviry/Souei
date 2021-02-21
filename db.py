from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///./data/proxies.db', echo=False)
sess_maker = sessionmaker(bind=engine)
