from sqlalchemy import Column, Integer, String, ForeignKey, SmallInteger
from sqlalchemy.orm import relationship

from database import Base


class User(Base):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True, unique=True, nullable=False)
    subject = Column(SmallInteger)
    difficult = Column(SmallInteger)

    history_records = relationship('HistoryRecord', back_populates='user')


class HistoryRecord(Base):

    __tablename__ = 'history_records'

    id = Column(Integer, primary_key=True, index=True)
    user = relationship('User', back_populates='history_records')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    message = Column(String, nullable=False)
    role = Column(SmallInteger, nullable=False)
