from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    medicines = db.relationship("Medicine", backref="user", lazy=True, cascade="all, delete-orphan")
    allergies = db.relationship("Allergy", backref="user", lazy=True, cascade="all, delete-orphan")
    records = db.relationship("MedicalRecord", backref="user", lazy=True, cascade="all, delete-orphan")
    events = db.relationship("HealthEvent", backref="user", lazy=True, cascade="all, delete-orphan")
    vitals = db.relationship("Vital", backref="user", lazy=True, cascade="all, delete-orphan")
    diet_charts = db.relationship("DietChart", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "age": self.age}


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(50))
    frequency = db.Column(db.String(50))
    purpose = db.Column(db.String(200))
    notes = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "name": self.name,
            "dosage": self.dosage, "frequency": self.frequency,
            "purpose": self.purpose, "notes": self.notes,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Allergy(db.Model):
    __tablename__ = "allergies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    severity = db.Column(db.String(50), default="moderate")
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "name": self.name,
            "severity": self.severity, "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class MedicalRecord(db.Model):
    __tablename__ = "medical_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    document_name = db.Column(db.String(255))
    document_type = db.Column(db.String(50))
    extracted_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "extracted_text": self.extracted_text,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class HealthEvent(db.Model):
    __tablename__ = "health_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "title": self.title, "description": self.description,
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AuthEvent(db.Model):
    __tablename__ = "auth_events"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    email = db.Column(db.String(120))
    event_type = db.Column(db.String(30))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "email": self.email,
            "event_type": self.event_type, "ip_address": self.ip_address,
            "user_agent": self.user_agent, 
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Vital(db.Model):
    __tablename__ = "vitals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    kind = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20))
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "kind": self.kind, "value": self.value, "unit": self.unit,
            "notes": self.notes,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None
        }


class DietChart(db.Model):
    __tablename__ = "diet_charts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    health_condition = db.Column(db.String(150))
    breakfast = db.Column(db.Text)
    lunch = db.Column(db.Text)
    dinner = db.Column(db.Text)
    snacks = db.Column(db.Text)
    foods_to_avoid = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "health_condition": self.health_condition,
            "breakfast": self.breakfast, "lunch": self.lunch,
            "dinner": self.dinner, "snacks": self.snacks,
            "foods_to_avoid": self.foods_to_avoid,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    target_conditions = db.Column(db.String(255))
    instructions = db.Column(db.Text)
    duration = db.Column(db.String(50))
    level = db.Column(db.String(50))
    pose_key = db.Column(db.String(30))

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "category": self.category,
            "description": self.description, "target_conditions": self.target_conditions,
            "instructions": self.instructions, "duration": self.duration,
            "level": self.level, "pose_key": self.pose_key
        }