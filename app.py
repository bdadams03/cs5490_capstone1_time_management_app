
from flask import Flask, render_template, request, redirect, send_file, flash # pyright: ignore[reportMissingImports]
from apscheduler.schedulers.background import BackgroundScheduler # pyright: ignore[reportMissingImports]
from database import SessionLocal
from sqlalchemy import desc
from models import Task, TaskHistory
import datetime, json, secrets

app = Flask(__name__)

app.secret_key = secrets.token_hex(16) #DEVONLY: generates random 32 character hex key (needed for flash)

navbar={'/':'Home','/tasks':'Tasks','/analytics':'Analytics','/weekly':'Weekly','/export':'Export','/import':'Import'}

def focus_check():
    session=SessionLocal()
    now=datetime.datetime.now()
    weekday=now.strftime("%a")[:3]
    tasks=session.query(Task).filter(Task.weekday==weekday).all()
    for t in tasks:
        start=t.start_time
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
    now=datetime.datetime.today()
    tasks=s.query(Task).filter(Task.start_date==now.date()).order_by(Task.start_time).all()
    alphalist = []
    for t in tasks:
        alphalist.append(t)
    category_sort = sorted(alphalist, key=lambda Task: Task.category)
    selected = request.args.get('filter', 'none')
    if selected == 'category':
        items = category_sort
    else:
        items = tasks
    return render_template("dashboard.html",tasks=tasks,navbar=navbar,items=items, selected=selected )

@app.route("/tasks",methods=["GET","POST"])
def tasks():
    s=SessionLocal()
    if request.method=="POST":
        title=request.form.get('title', '').strip()
        start_time_string=request.form.get('start_time', '').strip()
        start_date_string=request.form.get('start_date', '').strip()
        duration_minutes=request.form.get('duration', '').strip()
        checkin_interval=request.form.get('interval', '').strip()
        snooze_limit=request.form.get('snooze', '').strip()
        category=request.form.get('category', '').strip()

        
        error = None
        
        if not title:
            error = "Task title is required."

        if not error:
            try:
                start_time = datetime.datetime.strptime(start_time_string, '%H:%M').time()
            except (ValueError, TypeError):
                error = "Invalid time format. Please Use HH:MM (24-hour format)."

        if not error:
            try:
                start_date = datetime.datetime.strptime(start_date_string, '%m/%d/%Y').date()
            except (ValueError, TypeError):
                error = "Invalid date format. Please use MM/DD/YYYY."
                
        if not error:
            try:
                duration_val = int(duration_minutes) if duration_minutes else None
                interval_val = int(checkin_interval) if checkin_interval else None
                snooze_val = int(snooze_limit) if snooze_limit else None
            except ValueError:
                error = "Duration (minutes), checkin interval (minutes), and snooze limit (minutes) must be integers."
                
        if error:
            flash(error, 'error')
            return (render_template("tasks.html",
                                   tasks=s.query(Task).all(),
                                   title=title,
                                   start_date=start_date_string,
                                   start_time=start_time_string,
                                   duration_minutes=duration_minutes,
                                   checkin_interval=checkin_interval,
                                   snooze_limit=snooze_limit,
                                   category=category,
                                   navbar=navbar))
            
           
        t=Task(
            title=title,
            weekday=start_date.strftime('%a'),
            start_time=start_time,
            start_date=start_date,
            duration_minutes=duration_val,
            checkin_interval=interval_val,
            snooze_limit=snooze_val,
            category=category
        )
        s.add(t); s.commit()
        flash("Task added sucessfully")
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

    now = datetime.datetime.today()
    thirtyago = now - datetime.timedelta(days = 30)
    tasks=s.query(Task).filter(Task.start_date >= thirtyago.date(), Task.start_date <= now.date()).order_by(desc(Task.start_date)).all()
    data=[]
    for t in tasks:
        data.append((t.title,totals.get(t.id,0),t.start_date))

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
