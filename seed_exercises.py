"""Seed exercises with pose_key linking to POSE_RULES for camera-based practice."""
from app import app
from models import db, Exercise

EXERCISES = [
    # === YOGA (all linked to pose_engine rules) ===
    ("Surya Namaskar", "Yoga",
     "12-pose sun salutation flow linking breath with movement.",
     "general fitness, flexibility, energy",
     "1. Mountain pose, palms at heart.\n2. Inhale, arms up.\n3. Fold forward.\n4. Step back to plank.\n5. Cobra.\n6. Downward dog.\n7. Reverse sequence.\nRepeat 3-5 rounds.",
     "10 min", "intermediate", None),

    ("Bhujangasana (Cobra Pose)", "Yoga",
     "Gentle back-bend opening chest and strengthening spine.",
     "back pain, posture, spine flexibility",
     "1. Lie face down.\n2. Hands under shoulders, elbows close.\n3. Press up, lifting chest.\n4. Keep hips grounded.\n5. Hold 20 seconds.",
     "5 min", "beginner", "cobra"),

    ("Vrikshasana (Tree Pose)", "Yoga",
     "Standing balance improving focus and leg strength.",
     "balance, focus, leg weakness",
     "1. Stand tall.\n2. Shift weight to left foot.\n3. Right sole on inner left thigh or calf.\n4. Palms at heart or overhead.\n5. Hold 30 sec, switch.",
     "5 min", "beginner", "tree"),

    ("Tadasana (Mountain Pose)", "Yoga",
     "Foundation standing pose for alignment and posture.",
     "posture, balance, focus",
     "1. Stand feet together.\n2. Roll shoulders back.\n3. Arms at sides, palms forward.\n4. Gaze forward, breathe.",
     "3 min", "beginner", "mountain"),

    ("Virabhadrasana II (Warrior II)", "Yoga",
     "Powerful standing pose building leg strength.",
     "leg strength, hip mobility, balance",
     "1. Step feet wide, right foot forward.\n2. Bend right knee to 90°.\n3. Arms parallel to floor.\n4. Gaze over right hand.",
     "5 min", "beginner", "warrior2"),

    ("Utkatasana (Chair Pose)", "Yoga",
     "Squat-like pose strengthening legs and core.",
     "leg strength, core, posture",
     "1. Feet together.\n2. Bend knees deeply.\n3. Arms overhead.\n4. Weight in heels.",
     "3 min", "intermediate", "chair"),

    ("Adho Mukha Svanasana (Downward Dog)", "Yoga",
     "Inverted V pose stretching whole body.",
     "full-body stretch, hamstrings, back",
     "1. Hands and knees.\n2. Tuck toes, lift hips high.\n3. Straighten legs.\n4. Press hands down.",
     "5 min", "beginner", "downdog"),

    # === STRENGTH ===
    ("Plank Hold", "Strength",
     "Static core hold in push-up position.",
     "core weakness, back pain, posture",
     "1. Push-up position, hands under shoulders.\n2. Body in straight line.\n3. Engage core.\n4. Hold 30-60 seconds.",
     "3 min", "intermediate", "plank"),

    ("Bodyweight Squats", "Strength",
     "Fundamental lower-body movement.",
     "leg weakness, mobility, diabetes",
     "1. Feet shoulder-width.\n2. Lower hips back and down.\n3. Chest up, knees over toes.\n4. 3 sets of 12.",
     "5 min", "beginner", None),

    ("Wall Push-Ups", "Strength",
     "Beginner-friendly upper-body strength.",
     "upper body weakness, elderly, rehab",
     "1. Stand arm's length from wall.\n2. Palms at shoulder height.\n3. Bend elbows, lean in.\n4. 3 sets of 10.",
     "5 min", "beginner", None),

    ("Glute Bridge", "Strength",
     "Hip lift strengthening glutes and lower back.",
     "back pain, weak glutes, hip stability",
     "1. Lie on back, knees bent.\n2. Squeeze glutes, lift hips.\n3. Pause at top.\n4. 3 sets of 12.",
     "4 min", "beginner", None),

    # === STRETCHING ===
    ("Cat-Cow Stretch", "Stretching",
     "Alternating spinal flexion and extension.",
     "back pain, stiffness, posture",
     "1. Hands and knees.\n2. Inhale — drop belly, lift chest (Cow).\n3. Exhale — round spine (Cat).\n4. Repeat 8-10 rounds.",
     "5 min", "beginner", None),

    ("Standing Forward Fold", "Stretching",
     "Hamstring and lower-back release.",
     "tight hamstrings, back tension",
     "1. Stand feet hip-width.\n2. Hinge and fold forward.\n3. Let head hang, bend knees as needed.\n4. Hold 1-2 minutes.",
     "3 min", "beginner", None),

    ("Seated Spinal Twist", "Stretching",
     "Gentle rotation for spine and digestion.",
     "back stiffness, digestion",
     "1. Sit with legs extended.\n2. Bend right knee, cross over left thigh.\n3. Twist right, hold 30 sec.\n4. Switch sides.",
     "4 min", "beginner", None),

    # === BREATHING ===
    ("Anulom Vilom (Alternate Nostril)", "Breathing",
     "Pranayama balancing nervous system.",
     "stress, anxiety, blood pressure, focus",
     "1. Sit comfortably.\n2. Close right nostril, inhale left.\n3. Close left, exhale right.\n4. Continue 8 min.",
     "8 min", "beginner", None),

    ("Box Breathing (4-4-4-4)", "Breathing",
     "Navy-SEAL technique for rapid calm.",
     "anxiety, stress, insomnia",
     "1. Inhale 4 counts.\n2. Hold 4.\n3. Exhale 4.\n4. Hold 4. Repeat 5 min.",
     "5 min", "beginner", None),

    ("Bhramari (Bee Breath)", "Breathing",
     "Humming exhale that soothes the mind.",
     "anxiety, insomnia, blood pressure",
     "1. Sit, close eyes.\n2. Fingers on ear flaps.\n3. Inhale deeply.\n4. Exhale humming like a bee.\n5. Repeat 10 rounds.",
     "6 min", "beginner", None),

    ("4-7-8 Breathing", "Breathing",
     "Dr. Weil's calming breath for sleep.",
     "insomnia, anxiety, racing thoughts",
     "1. Tongue behind upper teeth.\n2. Exhale fully.\n3. Inhale 4 counts.\n4. Hold 7.\n5. Exhale 8. Repeat 4 cycles.",
     "4 min", "beginner", None),

    # === RELAXATION ===
    ("Balasana (Child's Pose)", "Relaxation",
     "Kneeling forward-fold resting pose.",
     "stress, anxiety, back tension",
     "1. Kneel, big toes touching.\n2. Sit back on heels.\n3. Fold forward, arms extended.\n4. Rest forehead down. Hold 2-3 min.",
     "3 min", "beginner", None),

    ("Shavasana (Corpse Pose)", "Relaxation",
     "Full-body relaxation lying flat.",
     "insomnia, fatigue, blood pressure",
     "1. Lie flat on back.\n2. Arms by sides, palms up.\n3. Close eyes.\n4. Scan body toe to head. Stay 10 min.",
     "10 min", "beginner", None),

    ("Progressive Muscle Relaxation", "Relaxation",
     "Systematically tense and release muscles.",
     "chronic tension, anxiety, insomnia",
     "1. Lie down.\n2. Tense feet 5 sec, release.\n3. Move up: calves, thighs, glutes, belly, chest, arms, face.\n4. End with full-body scan.",
     "12 min", "beginner", None),

    # === MOBILITY ===
    ("Neck Rolls", "Mobility",
     "Slow rotations for neck and upper spine.",
     "neck stiffness, screen fatigue, headaches",
     "1. Sit tall.\n2. Drop chin to chest.\n3. Slowly roll to right, back, left, down.\n4. 5 rolls each direction.",
     "2 min", "beginner", None),

    ("Shoulder Rolls", "Mobility",
     "Simple shoulder mobility drill.",
     "shoulder tension, posture, desk fatigue",
     "1. Sit or stand tall.\n2. Lift shoulders to ears.\n3. Roll back and down.\n4. 10 rolls backward, then forward.",
     "2 min", "beginner", None),

    ("Hip Circles", "Mobility",
     "Warm up hips with gentle rotation.",
     "hip stiffness, lower back tension",
     "1. Hands on hips, feet shoulder-width.\n2. Circle hips clockwise, keep torso still.\n3. 10 circles, reverse.",
     "3 min", "beginner", None),
]


with app.app_context():
    if Exercise.query.count() == 0:
        for title, category, description, target, instructions, duration, level, pose_key in EXERCISES:
            db.session.add(Exercise(
                title=title, category=category, description=description,
                target_conditions=target, instructions=instructions,
                duration=duration, level=level, pose_key=pose_key,
            ))
        db.session.commit()
        print(f"✓ Seeded {len(EXERCISES)} exercises ({sum(1 for e in EXERCISES if e[7])} with camera detection).")
    else:
        print(f"Exercises already seeded ({Exercise.query.count()} rows).")