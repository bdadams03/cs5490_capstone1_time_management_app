
from database import engine
from models import Base, Task, TaskHistory
from sqlalchemy.orm import sessionmaker # pyright: ignore[reportMissingImports]
import datetime, random

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
s = Session()


weekdays=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
cats=["Category A","Category B","Category C","Category D","Category E"]
begin_datetime = datetime.datetime(2025, 10, 19)
end_datetime = datetime.datetime(2025, 12, 19)

def rand_datetime(start, end):
    delta = end - start
    random_seconds = random.randrange(int(delta.total_seconds()))
    return_datetime = (start+datetime.timedelta(seconds=random_seconds))
    return return_datetime

task_ids=[]
for i in range(1,21):
    randDT = rand_datetime(begin_datetime, end_datetime)
    title=f"Task {i}"
    weekday = randDT.strftime('%a')
    random_time = randDT.time()
    random_date = randDT.date()
    duration=random.choice([30,45,60,90,120])
    interval=random.choice([10,15,20,30])
    snooze=random.choice([1,2,3])
    cat=random.choice(cats)

    t=Task(title=title,weekday=weekday,start_time=random_time,start_date=random_date,
           duration_minutes=duration,checkin_interval=interval,
           snooze_limit=snooze,category=cat)
    s.add(t); s.commit()
    task_ids.append(t.id)

for tid in task_ids:
    for _ in range(random.randint(5,10)):
        h=TaskHistory(task_id=tid,status="check_in_triggered")
        s.add(h)
    s.commit()
