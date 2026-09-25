import sys
import os
from datetime import datetime, timedelta
from app import app, db
from models import User, Vital

def seed_vitals():
    with app.app_context():
        user = User.query.first()
        if not user:
            print("No user found!")
            return
            
        # Delete existing vitals for clean seed
        Vital.query.filter_by(user_id=user.id).delete()
        
        now = datetime.utcnow()
        vitals = [
            # Heart Rate
            Vital(user_id=user.id, kind="Heart Rate", value="72", unit="bpm", recorded_at=now - timedelta(days=3)),
            Vital(user_id=user.id, kind="Heart Rate", value="75", unit="bpm", recorded_at=now - timedelta(days=2)),
            Vital(user_id=user.id, kind="Heart Rate", value="78", unit="bpm", recorded_at=now - timedelta(days=1)),
            Vital(user_id=user.id, kind="Heart Rate", value="71", unit="bpm", recorded_at=now),
            
            # Blood Pressure
            Vital(user_id=user.id, kind="Blood Pressure", value="120/80", unit="mmHg", recorded_at=now - timedelta(days=3)),
            Vital(user_id=user.id, kind="Blood Pressure", value="122/82", unit="mmHg", recorded_at=now - timedelta(days=2)),
            Vital(user_id=user.id, kind="Blood Pressure", value="118/79", unit="mmHg", recorded_at=now - timedelta(days=1)),
            Vital(user_id=user.id, kind="Blood Pressure", value="121/81", unit="mmHg", recorded_at=now),
            
            # Temperature
            Vital(user_id=user.id, kind="Temperature", value="36.5", unit="°C", recorded_at=now - timedelta(days=3)),
            Vital(user_id=user.id, kind="Temperature", value="36.6", unit="°C", recorded_at=now - timedelta(days=2)),
            Vital(user_id=user.id, kind="Temperature", value="36.4", unit="°C", recorded_at=now - timedelta(days=1)),
            Vital(user_id=user.id, kind="Temperature", value="36.7", unit="°C", recorded_at=now),
            
            # Weight
            Vital(user_id=user.id, kind="Weight", value="70.5", unit="kg", recorded_at=now - timedelta(days=3)),
            Vital(user_id=user.id, kind="Weight", value="70.4", unit="kg", recorded_at=now - timedelta(days=2)),
            Vital(user_id=user.id, kind="Weight", value="70.6", unit="kg", recorded_at=now - timedelta(days=1)),
            Vital(user_id=user.id, kind="Weight", value="70.3", unit="kg", recorded_at=now)
        ]
        
        db.session.bulk_save_objects(vitals)
        db.session.commit()
        print("Vitals seeded successfully!")

if __name__ == "__main__":
    seed_vitals()
