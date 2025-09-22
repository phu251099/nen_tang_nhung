from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

user = 'postgres'
password = 'thaco1234'
host = 'localhost'
port = '5432'
database = 'test'

# Tạo connection string kiểu cũ (chuỗi URL)
DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection_str:
        print('Successfully connected to the PostgreSQL database')
except Exception as ex:
    print(f'Sorry failed to connect: {ex}')

# khoi tao base
Base = declarative_base()
# Định nghĩa Session
SessionLocal = sessionmaker(bind=engine)