
from database import engine
from models import Base, Task, TaskHistory
from sqlalchemy.orm import sessionmaker # pyright: ignore[reportMissingImports]
import datetime, random

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
s = Session()


weekdays=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
cats=["Category A","Category B","Category C","Category D","Category E"]
begin_date = datetime.datetime(2025, 10, 19)
end_date = datetime.datetime(2025, 12, 19)

def rand_date(start, end):
    delta = end - start
    random_days = random.randrange(delta.days)
    return (start + datetime.timedelta(days = random_days)).datetime()

task_ids=[]
for i in range(1,21):
    title=f"Task {i}"
    weekday=random.choice(weekdays)
    hour=random.choice([8,9,10,13,14,15,17,18,19])
    minute=random.choice([0,15,30,45])
    random_days = rand_date(begin_date, end_date)
    start=f"{hour:02d}:{minute:02d}"
    duration=random.choice([30,45,60,90,120])
    interval=random.choice([10,15,20,30])
    snooze=random.choice([1,2,3])
    cat=random.choice(cats)

    t=Task(title=title,weekday=weekday,start_time=start, start_date=random_days,
           duration_minutes=duration,checkin_interval=interval,
           snooze_limit=snooze,category=cat)
    s.add(t); s.commit()
    task_ids.append(t.id)

for tid in task_ids:
    for _ in range(random.randint(5,10)):
        h=TaskHistory(task_id=tid,status="check_in_triggered")
        s.add(h)
    s.commit()
