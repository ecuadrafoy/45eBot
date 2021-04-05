from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import DATETIME, INTEGER, TEXT
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.schema import PrimaryKeyConstraint
from sqlalchemy.sql.sqltypes import DATE
import sqlite3

Base = declarative_base()

class Event(Base):
    __tablename__ = 'event'
    __table_args__= {'sqlite_autoincrement': True}
    id = Column(INTEGER, primary_key=True, nullable=False)
    name = Column(TEXT)
    server = Column(TEXT)
    date = Column(DATETIME)
    event_type = Column(TEXT)

class Attendance(Base):
    __tablename__ = 'attendance'
    __table_args__= {'sqlite_autoincrement': True}
    id = Column(INTEGER, primary_key=True, nullable=False)
    member_id = Column(INTEGER)
    member_name = Column(TEXT)
    event_id = Column(INTEGER)

class Member(Base):
    __tablename__ = 'member'
    id = Column(INTEGER, primary_key=True, nullable=False)
    name  = Column(TEXT)
    role = Column(TEXT)

class MoonDeath(Base):
    __tablename__ = 'killmoon'
    id = Column(INTEGER, primary_key=True, nullable=False)
    member_id = Column(TEXT)
    name = Column(TEXT)

class DeathList(Base):
    __tablename__ = 'deathlist'
    id = Column(INTEGER, primary_key=True, nullable=False)
    assassin_id = Column(TEXT)
    assasin_name = Column(TEXT)
    target_id = Column(TEXT)
    target_name = Column(TEXT)
