from sqlalchemy import Column, String, Text, BigInteger, Boolean, Integer

from sqlalchemy.orm import DeclarativeBase

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine("sqlite+aiosqlite:///sqlite3.db", echo=True)

async_session = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: int = Column(BigInteger, primary_key=True)
    name: str = Column(String(20))
    is_admin: bool = Column(Boolean, default=False)
    is_manager: bool = Column(Boolean, default=False)
    username: str = Column(String(33))


class Stock(Base):
    __tablename__="stocks"

    stock_id: int = Column(Integer, primary_key=True, autoincrement=True)
    title: str = Column(String(100))
    message_id: int = Column(BigInteger)
    photo_id: str = Column(String(300))
    caption: str = Column(Text)



async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)