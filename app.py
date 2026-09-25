from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from functools import wraps
from datetime import datetime, date
from io import BytesIO
import os, re

from config import Config
from models import db, User, Medicine, Allergy, MedicalRecord, HealthEvent, Exercise, Vital, DietChart, AuthEvent
from ocr_engine import extract_text_from_file, parse_medical_fields
from conflict_engine import check_conflicts, suggest_alternatives
from ai_assistant import answer_query, generate_diet_and_magnet

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs("database", exist_ok=True)

with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "unauthorized"}), 401
            return redirect(url_for("auth"))
        return f(*a, **kw)
    return wrap


def current_user():
    return User.query.get(session.get("user_id"))


def admin_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        u = current_user()
        if not u or not getattr(u, 'is_admin', False):
            if request.path.startswith("/api/"):
                return jsonify({"error": "forbidden"}), 403
            return "Forbidden", 403
        return f(*a, **kw)
    return wrap


def log_auth_event(email, event_type, user_id=None):
    ip = request.remote_addr
    ua = request.user_agent.string if request.user_agent else ""
    ev = AuthEvent(user_id=user_id, email=email, event_type=event_type, ip_address=ip, user_agent=ua)
    db.session.add(ev)
    db.session.commit()


def parse_date(s):
    if not s: return None
    try: return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception: return None


def freq_to_times(freq: str):
    freq = (freq or "").lower()
    presets = {
        "once": ["09:00"], "od": ["09:00"], "daily": ["09:00"],
        "bd": ["09:00", "21:00"], "twice": ["09:00", "21:00"],
        "tds": ["08:00", "14:00", "20:00"], "tid": ["08:00", "14:00", "20:00"],
        "qid": ["08:00", "12:00", "16:00", "20:00"], "hs": ["22:00"],
    }
    for k, v in presets.items():
        if k in freq: return v
    m = re.search(r"(\d+)\s*(?:times?|x)", freq)
    if m:
        n = int(m.group(1))
        return {1:["09:00"], 2:["09:00","21:00"],
                3:["08:00","14:00","20:00"], 4:["08:00","12:00","16:00","20:00"]}.get(n, ["09:00"])
    return ["09:00"]


# ==================== PUBLIC ====================
@app.route("/")
def index(): return render_template("index.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        mode = request.form.get("mode", "login")
        email = request.form["email"].lower().strip()
        pw = request.form["password"]
        if mode == "signup":
            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "error")
                return redirect(url_for("auth"))
            
            is_first_user = User.query.count() == 0
            u = User(name=request.form.get("name", "User"), email=email,
                     age=request.form.get("age") or None, is_admin=is_first_user)
            u.set_password(pw)
            db.session.add(u); db.session.commit()
            session["user_id"] = u.id
            log_auth_event(email, "signup", u.id)
            return redirect(url_for("dashboard"))
            
        u = User.query.filter_by(email=email).first()
        if not u or not u.check_password(pw):
            flash("Invalid email or password.", "error")
            log_auth_event(email, "login_fail", getattr(u, 'id', None))
            return redirect(url_for("auth"))
            
        session["user_id"] = u.id
        log_auth_event(email, "login_success", u.id)
        return redirect(url_for("dashboard"))
    return render_template("auth.html")

@app.route("/logout")
def logout():
    uid = session.get("user_id")
    if uid:
        u = User.query.get(uid)
        if u: log_auth_event(u.email, "logout", uid)
    session.clear()
    return redirect(url_for("index"))


# ==================== PAGES ====================
@app.route("/dashboard")
@login_required
def dashboard():
    u = current_user()
    stats = {
        "medicines": Medicine.query.filter_by(user_id=u.id, is_active=True).count(),
        "allergies": Allergy.query.filter_by(user_id=u.id).count(),
        "records":   MedicalRecord.query.filter_by(user_id=u.id).count(),
        "events":    HealthEvent.query.filter_by(user_id=u.id).count(),
    }
    return render_template("dashboard.html", user=u, stats=stats)

@app.route("/scanner")
@login_required
def scanner(): return render_template("scanner.html", user=current_user())

@app.route("/medicines")
@login_required
def medicines_page(): return render_template("medicines.html", user=current_user())

@app.route("/allergies")
@login_required
def allergies_page(): return render_template("allergies.html", user=current_user())

@app.route("/schedule")
@login_required
def schedule_page(): return render_template("schedule.html", user=current_user())

@app.route("/vitals")
@login_required
def vitals_page(): return render_template("vitals.html", user=current_user())

@app.route("/chart")
@login_required
def chart_page(): return render_template("chart.html", user=current_user())

@app.route("/exercises")
@login_required
def exercises_page(): return render_template("exercises.html", user=current_user())

@app.route("/ai")
@login_required
def ai_page(): return render_template("ai.html", user=current_user())

@app.route("/diet")
@login_required
def diet_page(): return render_template("diet.html", user=current_user())

@app.route("/profile")
@login_required
def profile_page(): return render_template("profile.html", user=current_user())

@app.route("/settings")
@login_required
def settings_page(): return render_template("settings.html", user=current_user())


# ==================== MEDICINES API ====================
@app.route("/api/medicines", methods=["GET"])
@login_required
def list_medicines():
    meds = Medicine.query.filter_by(user_id=session["user_id"]).order_by(Medicine.created_at.desc()).all()
    return jsonify([m.to_dict() for m in meds])

@app.route("/api/medicines", methods=["POST"])
@login_required
def create_medicine():
    d = request.get_json()
    u = current_user()
    m = Medicine(user_id=u.id, name=d["name"], dosage=d.get("dosage"),
                 frequency=d.get("frequency"), purpose=d.get("purpose"), notes=d.get("notes"),
                 start_date=parse_date(d.get("start_date")), end_date=parse_date(d.get("end_date")),
                 is_active=d.get("is_active", True))
    db.session.add(m); db.session.commit()
    allergies = [a.name for a in u.allergies]
    other_meds = [x.name for x in u.medicines if x.id != m.id]
    conflicts = check_conflicts(m.name, allergies, other_meds)
    if conflicts:
        rule_alts = suggest_alternatives(m.name, allergies)
        try:
            from ai_assistant import ai_alternatives
            final_alts = ai_alternatives(m.name, allergies, rule_alts["alternatives"])
        except Exception:
            final_alts = rule_alts
            
        for c in conflicts:
            c["alternatives"] = final_alts.get("alternatives", rule_alts["alternatives"])
            
    return jsonify({"medicine": m.to_dict(), "conflicts": conflicts}), 201

@app.route("/api/medicines/<int:mid>", methods=["PUT"])
@login_required
def update_medicine(mid):
    m = Medicine.query.filter_by(id=mid, user_id=session["user_id"]).first_or_404()
    d = request.get_json()
    for f in ["name","dosage","frequency","purpose","notes","is_active"]:
        if f in d: setattr(m, f, d[f])
    if "start_date" in d: m.start_date = parse_date(d["start_date"])
    if "end_date" in d: m.end_date = parse_date(d["end_date"])
    db.session.commit()
    return jsonify(m.to_dict())

@app.route("/api/medicines/<int:mid>", methods=["DELETE"])
@login_required
def delete_medicine(mid):
    m = Medicine.query.filter_by(id=mid, user_id=session["user_id"]).first_or_404()
    db.session.delete(m); db.session.commit()
    return jsonify({"ok": True})

@app.route("/api/medicines/alternatives", methods=["POST"])
@login_required
def med_alternatives():
    d = request.get_json()
    u = current_user()
    allergies = [a.name for a in u.allergies]
    return jsonify(suggest_alternatives(d.get("name", ""), allergies))


# ==================== ALLERGIES API ====================
@app.route("/api/allergies", methods=["GET"])
@login_required
def list_allergies():
    return jsonify([a.to_dict() for a in Allergy.query.filter_by(user_id=session["user_id"]).all()])

@app.route("/api/allergies", methods=["POST"])
@login_required
def create_allergy():
    d = request.get_json()
    a = Allergy(user_id=session["user_id"], name=d["name"],
                severity=d.get("severity", "moderate"), notes=d.get("notes"))
    db.session.add(a); db.session.commit()
    return jsonify(a.to_dict()), 201

@app.route("/api/allergies/<int:aid>", methods=["PUT"])
@login_required
def update_allergy(aid):
    a = Allergy.query.filter_by(id=aid, user_id=session["user_id"]).first_or_404()
    d = request.get_json()
    for f in ["name","severity","notes"]:
        if f in d: setattr(a, f, d[f])
    db.session.commit()
    return jsonify(a.to_dict())

@app.route("/api/allergies/<int:aid>", methods=["DELETE"])
@login_required
def delete_allergy(aid):
    a = Allergy.query.filter_by(id=aid, user_id=session["user_id"]).first_or_404()
    db.session.delete(a); db.session.commit()
    return jsonify({"ok": True})


# ==================== OCR + DIET ====================
@app.route("/api/scan", methods=["POST"])
@login_required
def scan_document():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    path = os.path.join(app.config["UPLOAD_FOLDER"], f"{session['user_id']}_{f.filename}")
    f.save(path)
    
    # Try Anthropic AI Vision first for 10x faster and more accurate extraction
    from ocr_engine import extract_with_ai, extract_text_from_file, parse_medical_fields
    ai_result = extract_with_ai(path)
    
    if ai_result:
        text = ai_result.get("text", "[AI Extracted]")
        parsed = ai_result
    else:
        text = extract_text_from_file(path)
        parsed = parse_medical_fields(text)
        
    rec = MedicalRecord(user_id=session["user_id"], document_name=f.filename,
                        document_type=f.mimetype, extracted_text=text)
    db.session.add(rec)
    
    saved_items = []
    
    # Auto-save medicines
    medicines = parsed.get("medicines", [])
    for med in medicines:
        m = Medicine(user_id=session["user_id"], name=med.get("name", "Unknown"), 
                     dosage=med.get("dosage", ""), frequency=med.get("frequency", ""), 
                     notes="Auto-added from scan", is_active=True)
        db.session.add(m)
        saved_items.append(f"Medicine: {m.name}")
        
    # Auto-save allergies
    allergies = parsed.get("allergies_mentioned", [])
    for alg in allergies:
        existing = Allergy.query.filter_by(user_id=session["user_id"], name=alg).first()
        if not existing:
            a = Allergy(user_id=session["user_id"], name=alg, severity="moderate", 
                        notes="Auto-added from scan")
            db.session.add(a)
            saved_items.append(f"Allergy: {alg}")
            
    db.session.commit()
    
    return jsonify({"record_id": rec.id, "text": text, "parsed": parsed, "saved_items": saved_items})


@app.route("/api/diet/generate", methods=["POST"])
@login_required
def diet_generate():
    d = request.get_json()
    ocr_text = d.get("ocr_text", "")
    condition = d.get("condition", "General Health")
    result = generate_diet_and_magnet(ocr_text, condition)

    # persist to DB
    dc = DietChart(
        user_id=session["user_id"],
        health_condition=condition,
        breakfast=result["diet_chart"]["breakfast"],
        lunch=result["diet_chart"]["lunch"],
        dinner=result["diet_chart"]["dinner"],
        snacks=result["diet_chart"]["snacks"],
        foods_to_avoid=result["diet_chart"]["foods_to_avoid"],
    )
    db.session.add(dc); db.session.commit()
    result["diet_chart_id"] = dc.id
    return jsonify(result)


@app.route("/api/diet")
@login_required
def diet_list():
    charts = DietChart.query.filter_by(user_id=session["user_id"]).order_by(DietChart.created_at.desc()).all()
    return jsonify([c.to_dict() for c in charts])


# ==================== VITALS ====================
@app.route("/api/vitals", methods=["GET"])
@login_required
def list_vitals():
    kind = request.args.get("kind")
    q = Vital.query.filter_by(user_id=session["user_id"])
    if kind: q = q.filter_by(kind=kind)
    return jsonify([v.to_dict() for v in q.order_by(Vital.recorded_at.asc()).all()])

@app.route("/api/vitals", methods=["POST"])
@login_required
def create_vital():
    d = request.get_json()
    v = Vital(user_id=session["user_id"], kind=d["kind"], value=d["value"],
              unit=d.get("unit"), notes=d.get("notes"))
    db.session.add(v); db.session.commit()
    return jsonify(v.to_dict()), 201

@app.route("/api/vitals/<int:vid>", methods=["DELETE"])
@login_required
def delete_vital(vid):
    v = Vital.query.filter_by(id=vid, user_id=session["user_id"]).first_or_404()
    db.session.delete(v); db.session.commit()
    return jsonify({"ok": True})


# ==================== SCHEDULE / CHART / EXERCISES / AI / PROFILE ====================
@app.route("/api/schedule/today")
@login_required
def schedule_today():
    u = current_user()
    today = date.today()
    slots = []
    for m in u.medicines:
        if not m.is_active: continue
        if m.start_date and m.start_date > today: continue
        if m.end_date and m.end_date < today: continue
        for t in freq_to_times(m.frequency):
            slots.append({"medicine_id": m.id, "name": m.name,
                          "dosage": m.dosage or "", "time": t, "purpose": m.purpose or ""})
    slots.sort(key=lambda s: s["time"])
    return jsonify({"date": today.isoformat(), "slots": slots})

@app.route("/api/chart")
@login_required
def chart_data():
    u = current_user()
    return jsonify({
        "medicines": [m.to_dict() for m in u.medicines],
        "allergies": [a.to_dict() for a in u.allergies],
        "records":   [r.to_dict() for r in u.records],
        "events":    [e.to_dict() for e in u.events],
    })

@app.route("/api/exercises")
@login_required
def list_exercises():
    cat = request.args.get("category")
    q = Exercise.query
    if cat: q = q.filter_by(category=cat)
    return jsonify([e.to_dict() for e in q.all()])

@app.route("/api/ai/chat", methods=["POST"])
@login_required
def ai_chat():
    q = request.get_json().get("message", "").strip()
    if not q: return jsonify({"error": "empty"}), 400
    u = current_user()
    context = {
        "medicines": [m.to_dict() for m in u.medicines if m.is_active],
        "allergies": [a.to_dict() for a in u.allergies],
    }
    return jsonify({"reply": answer_query(q, context)})

@app.route("/api/profile", methods=["GET", "PUT"])
@login_required
def profile():
    u = current_user()
    if request.method == "PUT":
        d = request.get_json()
        u.name = d.get("name", u.name)
        if "age" in d: u.age = d.get("age")
        db.session.commit()
    return jsonify(u.to_dict())


# ==================== PDF ====================
@app.route("/api/report/pdf")
@login_required
def export_report():
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    u = current_user()
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("t", parent=styles["Title"], fontSize=22, textColor=colors.HexColor("#0f766e"))
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#0f172a"), spaceBefore=14)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    story = [
        Paragraph("MedBuddy Health Report", title_s),
        Paragraph(f"Generated for <b>{u.name}</b> on {datetime.now().strftime('%d %b %Y, %H:%M')}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph("Profile", h2),
    ]
    t = Table([["Name", u.name], ["Email", u.email], ["Age", str(u.age or '-')]], colWidths=[4*cm, 12*cm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f1f5f9")),
                           ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
                           ("PADDING", (0,0), (-1,-1), 6)]))
    story.append(t)

    story.append(Paragraph("Allergies", h2))
    if u.allergies:
        rows = [["Allergen","Severity","Notes"]] + [[a.name, a.severity or "-", a.notes or "-"] for a in u.allergies]
        t = Table(rows, colWidths=[5*cm, 3*cm, 8*cm])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#fee2e2")),
                               ("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),
                               ("PADDING",(0,0),(-1,-1),6)]))
        story.append(t)
    else:
        story.append(Paragraph("<i>No allergies recorded.</i>", styles["Normal"]))

    story.append(Paragraph("Active Medicines", h2))
    active = [m for m in u.medicines if m.is_active]
    if active:
        rows = [["Name","Dosage","Frequency","Purpose"]] + [[m.name, m.dosage or "-", m.frequency or "-", m.purpose or "-"] for m in active]
        t = Table(rows, colWidths=[4*cm, 3*cm, 4*cm, 5*cm])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#dcfce7")),
                               ("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),
                               ("PADDING",(0,0),(-1,-1),6)]))
        story.append(t)
    else:
        story.append(Paragraph("<i>No active medicines.</i>", styles["Normal"]))

    vitals = Vital.query.filter_by(user_id=u.id).order_by(Vital.recorded_at.desc()).limit(20).all()
    story.append(Paragraph("Recent Vitals", h2))
    if vitals:
        rows = [["Type","Value","Unit","Recorded"]] + [[v.kind.upper(), v.value, v.unit or "-",
                                                        v.recorded_at.strftime("%d %b %Y %H:%M")] for v in vitals]
        t = Table(rows, colWidths=[4*cm, 4*cm, 3*cm, 5*cm])
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e0e7ff")),
                               ("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),
                               ("PADDING",(0,0),(-1,-1),6)]))
        story.append(t)
    else:
        story.append(Paragraph("<i>No vitals recorded yet.</i>", styles["Normal"]))

    story.append(Spacer(1, 20))
    story.append(Paragraph("This report is generated by MedBuddy for informational purposes only and does not replace professional medical advice.", small))

    doc.build(story)
    buf.seek(0)
    return send_file(buf, mimetype="application/pdf", as_attachment=True,
                     download_name=f"medbuddy_report_{u.id}.pdf")


# ==================== POSE / YOGA ====================
from pose_engine import get_poses_for_condition, get_pose, all_poses, POSE_RULES

@app.route("/yoga")
@login_required
def yoga_page(): return render_template("yoga.html", user=current_user())

@app.route("/yoga/practice/<pose_key>")
@login_required
def yoga_practice(pose_key):
    pose = get_pose(pose_key)
    if not pose: return redirect(url_for("yoga_page"))
    return render_template("yoga_practice.html", user=current_user(), pose=pose, pose_key=pose_key)

@app.route("/api/yoga/recommendations")
@login_required
def yoga_recommendations():
    condition = request.args.get("condition", "")
    keys = get_poses_for_condition(condition)
    return jsonify([{"key": k, **POSE_RULES[k]} for k in keys if k in POSE_RULES])

@app.route("/api/yoga/all")
@login_required
def yoga_all():
    return jsonify(all_poses())


# ==================== ENHANCED ALTERNATIVES ====================
from ai_assistant import ai_alternatives

@app.route("/api/medicines/smart-alternatives", methods=["POST"])
@login_required
def smart_alternatives():
    d = request.get_json()
    u = current_user()
    allergies = [a.name for a in u.allergies]
    rule_result = suggest_alternatives(d.get("name", ""), allergies)
    enhanced = ai_alternatives(d.get("name", ""), allergies, rule_result["alternatives"])
    return jsonify({
        "medicine": d.get("name"),
        "rule_based": rule_result,
        "ai_enhanced": enhanced,
    })


# ==================== YOGA SESSION LOG ====================
@app.route("/api/yoga/log", methods=["POST"])
@login_required
def yoga_log():
    """Store a completed yoga session as a HealthEvent."""
    d = request.get_json()
    ev = HealthEvent(
        user_id=session["user_id"],
        title=f"Yoga: {d.get('pose_name', 'Practice')}",
        description=f"Held {d.get('hold_seconds', 0)}s. Accuracy: {d.get('accuracy', 0)}%.",
    )
    db.session.add(ev); db.session.commit()
    return jsonify({"ok": True, "event_id": ev.id})


@app.route("/exercise/practice/<int:eid>")
@login_required
def exercise_practice(eid):
    """Every exercise gets a camera view — AI Coach mode or Live Companion mode."""
    ex = Exercise.query.get_or_404(eid)
    pose = None
    generic_mode = None

    if ex.pose_key:
        from pose_engine import get_pose
        pose = get_pose(ex.pose_key)

    if not pose:
        from pose_engine import get_generic_mode
        generic_mode = get_generic_mode(ex.title)

    return render_template("exercise_practice.html",
                           user=current_user(),
                           exercise=ex.to_dict(),
                           pose=pose,
                           generic_mode=generic_mode)

# ==================== ADMIN DASHBOARD ====================
@app.route("/admin")
@login_required
@admin_required
def admin_page():
    return render_template("admin.html", user=current_user())

@app.route("/api/admin/users")
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    res = []
    for u in users:
        last_event = AuthEvent.query.filter_by(user_id=u.id, event_type="login_success").order_by(AuthEvent.created_at.desc()).first()
        res.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "age": u.age,
            "is_admin": getattr(u, 'is_admin', False),
            "medicines_count": Medicine.query.filter_by(user_id=u.id).count(),
            "allergies_count": Allergy.query.filter_by(user_id=u.id).count(),
            "vitals_count": Vital.query.filter_by(user_id=u.id).count(),
            "joined_date": u.created_at.isoformat() if u.created_at else None,
            "last_login": last_event.created_at.isoformat() if last_event else None
        })
    return jsonify(res)

@app.route("/api/admin/events")
@login_required
@admin_required
def admin_events():
    limit = request.args.get("limit", 100, type=int)
    events = AuthEvent.query.order_by(AuthEvent.created_at.desc()).limit(limit).all()
    return jsonify([e.to_dict() for e in events])


@app.route("/api/admin/stats")
@login_required
@admin_required
def admin_stats():
    from datetime import timedelta
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    
    total_users = User.query.count()
    active_today = db.session.query(AuthEvent.user_id).filter(
        AuthEvent.created_at >= today_start,
        AuthEvent.event_type == 'login_success'
    ).distinct().count()
    
    signups_week = AuthEvent.query.filter(
        AuthEvent.created_at >= week_start,
        AuthEvent.event_type == 'signup'
    ).count()
    
    failed_logins_today = AuthEvent.query.filter(
        AuthEvent.created_at >= today_start,
        AuthEvent.event_type == 'login_fail'
    ).count()
    
    return jsonify({
        "total_users": total_users,
        "active_today": active_today,
        "signups_this_week": signups_week,
        "failed_logins_today": failed_logins_today
    })

if __name__ == "__main__":
    app.run(debug=True)