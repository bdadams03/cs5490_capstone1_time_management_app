
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, ForeignKey
import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    weekday = Column(String)
    start_time = Column(Time)
    start_date = Column(Date)
    duration_minutes = Column(Integer)
    checkin_interval = Column(Integer)
    snooze_limit = Column(Integer)
    category = Column(String)

class TaskHistory(Base):
    __tablename__ = "task_history"
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
