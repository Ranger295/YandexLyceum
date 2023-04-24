import os
from sqlalchemy import Column, String, create_engine, Text
from sqlalchemy.orm import DeclarativeBase, Session

if not os.path.isfile("RotexData.db"):
    f = open("RotexData.db", mode='w')
    f.close()
sqlite_database = "sqlite:///RotexData.db"
engine = create_engine(sqlite_database)


class Base(DeclarativeBase):
    pass


class GUILDS(Base):
    __tablename__ = "GUILDS_DATA"
    GUILD_ID = Column(String, primary_key=True, index=True)
    LINKED_CHANNELS_ID = Column(Text)
    TG_LINKED_CHANNELS_ID = Column(Text)
    LINK_WAITING_CHANNEL_ID = Column(Text)
    TG_LINK_WATING_GROUP_ID = Column(Text)
    TG_LINK_WATING_CHANNEL_ID = Column(Text)


class GROUPS(Base):
    __tablename__ = "GROUPS_DATA"
    GROUP_ID = Column(Text, primary_key=True, index=True)
    LINKED_CHANNEL_ID = Column(Text)
    LINK_WAITING_GUILD_ID = Column(Text)


class TG_LINKED(Base):
    __tablename__ = "LINKED_GROUPS"
    CHANNEL_ID = Column(Text, primary_key=True, index=True)
    LINKED_CHANNEL_ID = Column(Text)


class LINKED(Base):
    __tablename__ = "LINKED_CHANNELS"
    CHANNEL_ID = Column(Text, primary_key=True, index=True)
    LINKED_CHANNELS_ID = Column(Text)


class WEBHOOKS(Base):
    __tablename__ = "WEBHOOKS"
    CHANNEL_ID = Column(Text, primary_key=True, index=True)
    WEBHOOK_URL = Column(Text)


Base.metadata.create_all(bind=engine)
with Session(autoflush=False, bind=engine) as db:
    datas = db.query(GUILDS).all()