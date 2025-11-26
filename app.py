
from flask import Flask, render_template, request, redirect, send_file # pyright: ignore[reportMissingImports]
from apscheduler.schedulers.background import BackgroundScheduler # pyright: ignore[reportMissingImports]
from database import SessionLocal
from models import Task, TaskHistory
import datetime, json

app = Flask(__name__)

navbar={'/':'Home','/tasks':'Tasks','/analytics':'Analytics','/weekly':'Weekly','/export':'Export','/import':'Import'}

def focus_check():
    session=SessionLocal()
    now=datetime.datetime.now()
    weekday=now.strftime("%a")[:3]
    tasks=session.query(Task).filter(Task.weekday==weekday).all()
    for t in tasks:
        start=datetime.datetime.strptime(t.start_time,"%H:%M").time()
        end=(datetime.datetime.combine(now.date(),start)+datetime.timedelta(minutes=t.duration_minutes)).time()
        if start<=now.time()<=end:
            session.add(TaskHistory(task_id=t.id,status="check_in_triggered"))
            session.commit()
    session.close()

scheduler=BackgroundScheduler()
scheduler.add_job(focus_check,"interval",minutes=1)
scheduler.start()

@app.route("/")
def home():
    s=SessionLocal()
    now=datetime.datetime.now()
    w=now.strftime("%a")[:3]
    tasks=s.query(Task).filter(Task.weekday==w).all()
    return render_template("dashboard.html",tasks=tasks,navbar=navbar)

@app.route("/tasks",methods=["GET","POST"])
def tasks():
    s=SessionLocal()
    if request.method=="POST":
        t=Task(
            title=request.form["title"],
            weekday=request.form["weekday"],
            start_time=request.form["start_time"],
            duration_minutes=int(request.form["duration"]),
            checkin_interval=int(request.form["interval"]),
            snooze_limit=int(request.form["snooze"]),
            category=request.form["category"]
        )
        s.add(t); s.commit()
        return redirect("/tasks")
    items=s.query(Task).all()
    return render_template("tasks.html",tasks=items,navbar=navbar)

@app.route("/analytics")
def analytics():
    s=SessionLocal()
    hist=s.query(TaskHistory).all()
    totals={}
    for h in hist:
        totals[h.task_id]=totals.get(h.task_id,0)+1

    tasks=s.query(Task).all()
    data=[]
    for t in tasks:
        data.append((t.title,totals.get(t.id,0)))

    return render_template("analytics.html",data=data,streak=5,consistency="80%",navbar=navbar)

@app.route("/weekly")
def weekly():
    s=SessionLocal()
    tasks=s.query(Task).all()
    grid={"Mon":[],"Tue":[],"Wed":[],"Thu":[],"Fri":[],"Sat":[],"Sun":[]}
    for t in tasks:
        grid[t.weekday].append(t)
    return render_template("weekly.html",grid=grid,navbar=navbar)

@app.route("/export")
def export_data():
    s=SessionLocal()
    tasks=[t.__dict__ for t in s.query(Task).all()]
    for item in tasks:
        item.pop("_sa_instance_state",None)
    hist=[h.__dict__ for h in s.query(TaskHistory).all()]
    for item in hist:
        item.pop("_sa_instance_state",None)
    data={"tasks":tasks,"history":hist}
    open("export.json","w").write(json.dumps(data))
    return send_file("export.json",download_name="export.json")

@app.route("/import",methods=["GET","POST"])
def import_data():
    if request.method=="POST":
        f=request.files["file"]
        data=json.load(f)
        s=SessionLocal()
        for t in data.get("tasks",[]):
            s.add(Task(
                title=t["title"],weekday=t["weekday"],start_time=t["start_time"],
                duration_minutes=t["duration_minutes"],checkin_interval=t["checkin_interval"],
                snooze_limit=t["snooze_limit"],category=t["category"]
            ))
        s.commit()
        return redirect("/tasks")
    return render_template("import.html",navbar=navbar)

if __name__=="__main__":
    app.run(debug=True)
