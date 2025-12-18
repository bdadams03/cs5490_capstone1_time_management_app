
from flask import Flask, render_template, request, redirect, send_file, flash, url_for # pyright: ignore[reportMissingImports]
from apscheduler.schedulers.background import BackgroundScheduler # pyright: ignore[reportMissingImports]
from database import SessionLocal
from sqlalchemy import desc
from models import Task, TaskHistory
import datetime, json, secrets

app = Flask(__name__)

app.secret_key = secrets.token_hex(16) #DEVONLY: generates random 32 character hex key (needed for flash)

navbar={'/':'Home','/tasks':'Tasks','/calendar':'Calendar','/analytics':'Analytics','/weekly':'Weekly','/export':'Export','/import':'Import'}


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
    
    selected = request.args.get('filter', 'none')

    
    now=datetime.datetime.today()
    tasks=s.query(Task).filter(Task.start_date==now.date()).order_by(Task.start_time).all()
    
    category_sort = sorted(tasks, key=lambda Task: Task.category)
    
    if selected == 'category':
        items = category_sort
    else:
        items = tasks
    return render_template("dashboard.html",tasks=tasks,navbar=navbar,items=items, selected=selected )

@app.route("/tasks",methods=["GET","POST"])
def tasks():
    s = SessionLocal()
     
    selected = request.args.get('filter', 'none')
    
    tasks=s.query(Task).order_by(Task.start_date).all()
    
    category_sort = sorted(tasks, key=lambda t: t.category)
    title_sort = sorted(tasks, key=lambda t: t.title)
    
    if selected == 'category':
        items=category_sort
    elif selected == 'title':
        items = title_sort
    else:
        items = tasks
        
    if request.method == "POST":
        title = request.form.get('title', '').strip()
        start_time_string = request.form.get('start_time', '').strip()
        start_date_string = request.form.get('start_date', '').strip()
        duration_minutes = request.form.get('duration', '').strip()
        checkin_interval = request.form.get('interval', '').strip()
        snooze_limit = request.form.get('snooze', '').strip()
        category = request.form.get('category', '').strip()
        
        error = []
        
        if not title:
            error.append("Task Title is required.")
        
        try:
            start_time = datetime.datetime.strptime(start_time_string, '%H:%M').time()
        except(ValueError, TypeError):
            error.append("Invalid time format. Please use HH:MM (24-hour format).")
            
        try:
            start_date = datetime.datetime.strptime(start_date_string, '%m/%d/%Y').date()
        except(ValueError, TypeError):
            error.append("Invalid date format. Please use MM/DD/YYYY.")
            
        if not duration_minutes:
            error.append("Duration is required.")
        
        try:
            duration_val = int(duration_minutes)
        except ValueError:
            error.append("Duration (minutes) must be an integer.")
            
        if not checkin_interval:
            error.append("Checkin Interval is required.")
            
        try:
            interval_val = int(checkin_interval)
        except ValueError:
            error.append("Checkin Interval (minutes) must be an integer.")
            
        if not snooze_limit:
            error.append("Snooze Limit is required.")
            
        try:
            snooze_val = int(checkin_interval)
        except ValueError:
            error.append("Snooze Limit must be an integer.")

        if category == '':
            error.append("Category is required.")
            
            
        if error:
            cleaned_errors = [e.strip() for e in error]
            error_string = '\n'.join(cleaned_errors).strip()
            flash(error_string, 'error')
            return render_template("tasks.html",
                                   items = items,
                                   selected=selected,
                                   title=title,
                                   start_date=start_date_string,
                                   start_time=start_time_string,
                                   duration_minutes=duration_minutes,
                                   checkin_interval=checkin_interval,
                                   snooze_limit=snooze_limit,
                                   category=category,
                                   navbar=navbar)
            
        
        t = Task(
            title=title,
            weekday=start_date.strftime('%a'),
            start_time=start_time,
            start_date=start_date,
            duration_minutes=duration_val,
            checkin_interval=interval_val,
            snooze_limit=snooze_val,
            category=category
        )
        s.add(t)
        s.commit()
        flash("Task added successfully", 'success')
        
        return redirect(url_for('tasks', filter=selected))
    
    return render_template("tasks.html",items=items,selected=selected,navbar=navbar)


@app.route("/calendar")
def calendar():
    s = SessionLocal()
    year = request.args.get('year', type=int, default=datetime.datetime.today().year)
    month = request.args.get('month', type=int, default=datetime.datetime.today().month)
    import calendar as cal
    first_day_weekday, days_in_month = cal.monthrange(year, month)
    
    tasks = s.query(Task).filter(
        Task.start_date >= datetime.date(year, month, 1),
        Task.start_date <= datetime.date(year, month, days_in_month)
    ).all()
    tasks_by_day = {}
    for t in tasks:
        day = t.start_date.day
        if day not in tasks_by_day:
            tasks_by_day[day] = []
        tasks_by_day[day].append(t)
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1 
    month_name = cal.month_name[month]
    return render_template("calendar.html", 
                           navbar=navbar,
                           year=year, 
                           month=month,
                           month_name=month_name,
                           first_day_weekday=first_day_weekday,
                           days_in_month=days_in_month,
                           tasks_by_day=tasks_by_day,
                           prev_month=prev_month,
                           prev_year=prev_year,
                           next_month=next_month,
                           next_year=next_year)

@app.route("/analytics")
def analytics():
    s=SessionLocal()
    selected = request.args.get('filter', 'none')
    hist=s.query(TaskHistory).all()
    totals={}
    for h in hist:
        totals[h.task_id]=totals.get(h.task_id,0)+1

    now = datetime.datetime.today()
    thirtyago = now - datetime.timedelta(days = 30)
    tasks=s.query(Task).filter(Task.start_date >= thirtyago.date(), Task.start_date <= now.date()).order_by(desc(Task.start_date)).all()
    data=[]
    for t in tasks:
        data.append((t.title,totals.get(t.id,0),t.start_date,t.category)) ##spot
    category_sort = sorted(data, key=lambda tup: tup[3])
    if selected == 'category':
        items = category_sort
    else:
        items = data
    return render_template("analytics.html",data=data,streak=5,consistency="80%",navbar=navbar,items=items,selected=selected)

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

