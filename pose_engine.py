"""
MedBuddy — Pose Rule Engine
Per-asana angle & alignment rules that the client-side MediaPipe pose detector
evaluates against user landmarks in real time.

Each rule set defines:
  - name, sanskrit, difficulty, hold_seconds
  - target_conditions (which health issues it helps)
  - checks: list of {landmark_pair, expected_angle_range, message}
"""

POSE_RULES = {
    "mountain": {
        "name": "Mountain Pose (Tadasana)",
        "sanskrit": "ताड़ासन",
        "difficulty": "beginner",
        "hold_seconds": 30,
        "target_conditions": ["posture", "balance", "focus"],
        "instructions": [
            "Stand tall with feet together, weight even.",
            "Roll shoulders back and down.",
            "Arms at sides, palms forward.",
            "Gaze forward, breathe steadily."
        ],
        "checks": [
            {
                "id": "spine_straight",
                "type": "vertical_alignment",
                "landmarks": ["nose", "left_hip", "right_hip"],
                "tolerance": 0.08,
                "ok_message": "✓ Spine aligned",
                "fix_message": "Straighten your spine — head over hips"
            },
            {
                "id": "shoulders_level",
                "type": "horizontal_alignment",
                "landmarks": ["left_shoulder", "right_shoulder"],
                "tolerance": 0.04,
                "ok_message": "✓ Shoulders level",
                "fix_message": "Level your shoulders — one is higher"
            },
            {
                "id": "arms_down",
                "type": "angle_range",
                "landmarks": ["left_shoulder", "left_elbow", "left_wrist"],
                "min_angle": 160,
                "max_angle": 200,
                "ok_message": "✓ Arms relaxed",
                "fix_message": "Let arms hang naturally at your sides"
            }
        ]
    },

    "warrior2": {
        "name": "Warrior II (Virabhadrasana II)",
        "sanskrit": "वीरभद्रासन II",
        "difficulty": "beginner",
        "hold_seconds": 30,
        "target_conditions": ["leg strength", "hip mobility", "balance"],
        "instructions": [
            "Step feet wide apart, right foot forward.",
            "Bend right knee to 90°, thigh parallel to floor.",
            "Extend arms parallel to floor, gaze over right hand.",
            "Keep back leg straight and strong."
        ],
        "checks": [
            {
                "id": "front_knee_90",
                "type": "angle_range",
                "landmarks": ["right_hip", "right_knee", "right_ankle"],
                "min_angle": 80,
                "max_angle": 100,
                "ok_message": "✓ Front knee at 90°",
                "fix_message": "Bend front knee more — aim for 90°"
            },
            {
                "id": "back_leg_straight",
                "type": "angle_range",
                "landmarks": ["left_hip", "left_knee", "left_ankle"],
                "min_angle": 165,
                "max_angle": 195,
                "ok_message": "✓ Back leg strong",
                "fix_message": "Straighten your back leg fully"
            },
            {
                "id": "arms_horizontal",
                "type": "horizontal_alignment",
                "landmarks": ["left_wrist", "right_wrist"],
                "tolerance": 0.05,
                "ok_message": "✓ Arms parallel to floor",
                "fix_message": "Lift arms to shoulder height, parallel to floor"
            },
            {
                "id": "torso_upright",
                "type": "vertical_alignment",
                "landmarks": ["nose", "left_hip", "right_hip"],
                "tolerance": 0.10,
                "ok_message": "✓ Torso stacked over hips",
                "fix_message": "Keep torso upright — don't lean forward"
            }
        ]
    },

    "tree": {
        "name": "Tree Pose (Vrikshasana)",
        "sanskrit": "वृक्षासन",
        "difficulty": "beginner",
        "hold_seconds": 30,
        "target_conditions": ["balance", "focus", "leg strength"],
        "instructions": [
            "Stand on left foot, shift weight into it.",
            "Place right sole on inner left thigh or calf (never on knee).",
            "Bring palms together at heart or overhead.",
            "Fix gaze on a still point ahead."
        ],
        "checks": [
            {
                "id": "standing_leg_straight",
                "type": "angle_range",
                "landmarks": ["left_hip", "left_knee", "left_ankle"],
                "min_angle": 165,
                "max_angle": 195,
                "ok_message": "✓ Standing leg strong",
                "fix_message": "Straighten standing leg — don't lock knee"
            },
            {
                "id": "foot_lifted",
                "type": "relative_height",
                "landmarks": ["right_knee", "left_knee"],
                "min_diff": 0.05,
                "ok_message": "✓ Foot lifted",
                "fix_message": "Lift right foot higher onto inner thigh or calf"
            },
            {
                "id": "hips_level",
                "type": "horizontal_alignment",
                "landmarks": ["left_hip", "right_hip"],
                "tolerance": 0.06,
                "ok_message": "✓ Hips level",
                "fix_message": "Level your hips — don't hike right hip up"
            },
            {
                "id": "torso_tall",
                "type": "vertical_alignment",
                "landmarks": ["nose", "left_hip", "right_hip"],
                "tolerance": 0.10,
                "ok_message": "✓ Standing tall",
                "fix_message": "Lengthen spine — crown of head reaches up"
            }
        ]
    },

    "chair": {
        "name": "Chair Pose (Utkatasana)",
        "sanskrit": "उत्कटासन",
        "difficulty": "intermediate",
        "hold_seconds": 30,
        "target_conditions": ["leg strength", "core", "posture"],
        "instructions": [
            "Stand with feet together.",
            "Bend knees deeply, sit hips back as if into a chair.",
            "Raise arms overhead, palms facing each other.",
            "Keep chest lifted, weight in heels."
        ],
        "checks": [
            {
                "id": "knees_bent",
                "type": "angle_range",
                "landmarks": ["left_hip", "left_knee", "left_ankle"],
                "min_angle": 90,
                "max_angle": 130,
                "ok_message": "✓ Great squat depth",
                "fix_message": "Sit deeper — bend knees more"
            },
            {
                "id": "arms_up",
                "type": "angle_range",
                "landmarks": ["left_hip", "left_shoulder", "left_wrist"],
                "min_angle": 150,
                "max_angle": 195,
                "ok_message": "✓ Arms reaching up",
                "fix_message": "Reach arms higher overhead"
            },
            {
                "id": "chest_lifted",
                "type": "angle_range",
                "landmarks": ["left_shoulder", "left_hip", "left_knee"],
                "min_angle": 60,
                "max_angle": 110,
                "ok_message": "✓ Chest lifted",
                "fix_message": "Lift chest — don't collapse forward"
            }
        ]
    },

    "cobra": {
        "name": "Cobra Pose (Bhujangasana)",
        "sanskrit": "भुजंगासन",
        "difficulty": "beginner",
        "hold_seconds": 20,
        "target_conditions": ["back pain", "posture", "spine flexibility"],
        "instructions": [
            "Lie face down, legs extended, tops of feet on floor.",
            "Place hands under shoulders, elbows close to body.",
            "Inhale, press hands down, lift chest.",
            "Keep hips grounded, shoulders relaxed."
        ],
        "checks": [
            {
                "id": "chest_lifted",
                "type": "relative_height",
                "landmarks": ["nose", "left_hip"],
                "min_diff": 0.15,
                "ok_message": "✓ Chest lifting nicely",
                "fix_message": "Lift chest higher — press hands down"
            },
            {
                "id": "elbows_bent",
                "type": "angle_range",
                "landmarks": ["left_shoulder", "left_elbow", "left_wrist"],
                "min_angle": 90,
                "max_angle": 160,
                "ok_message": "✓ Elbows soft",
                "fix_message": "Keep a slight bend in elbows — don't lock them"
            }
        ]
    },

    "downdog": {
        "name": "Downward Dog (Adho Mukha Svanasana)",
        "sanskrit": "अधोमुख श्वानासन",
        "difficulty": "beginner",
        "hold_seconds": 30,
        "target_conditions": ["full-body stretch", "back", "hamstrings"],
        "instructions": [
            "Start on hands and knees.",
            "Tuck toes, lift hips high, forming inverted V.",
            "Press hands down, straighten legs (or keep soft bend).",
            "Head between arms, gaze at feet."
        ],
        "checks": [
            {
                "id": "hips_high",
                "type": "relative_height",
                "landmarks": ["left_hip", "left_shoulder"],
                "min_diff": 0.08,
                "ok_message": "✓ Hips lifting high",
                "fix_message": "Lift hips higher — form an inverted V"
            },
            {
                "id": "arms_straight",
                "type": "angle_range",
                "landmarks": ["left_shoulder", "left_elbow", "left_wrist"],
                "min_angle": 160,
                "max_angle": 195,
                "ok_message": "✓ Arms strong",
                "fix_message": "Straighten arms fully"
            },
            {
                "id": "legs_active",
                "type": "angle_range",
                "landmarks": ["left_hip", "left_knee", "left_ankle"],
                "min_angle": 140,
                "max_angle": 195,
                "ok_message": "✓ Legs engaged",
                "fix_message": "Straighten legs more (or slight bend if tight)"
            }
        ]
    },

    "plank": {
        "name": "Plank Pose (Phalakasana)",
        "sanskrit": "फलकासन",
        "difficulty": "intermediate",
        "hold_seconds": 30,
        "target_conditions": ["core strength", "back pain", "posture"],
        "instructions": [
            "Start in push-up position.",
            "Hands under shoulders, body in straight line head to heels.",
            "Engage core, don't let hips sag or lift.",
            "Breathe steadily."
        ],
        "checks": [
            {
                "id": "body_straight",
                "type": "line_alignment",
                "landmarks": ["left_shoulder", "left_hip", "left_ankle"],
                "tolerance": 0.08,
                "ok_message": "✓ Body in straight line",
                "fix_message": "Straight line from head to heels — engage core"
            },
            {
                "id": "arms_straight",
                "type": "angle_range",
                "landmarks": ["left_shoulder", "left_elbow", "left_wrist"],
                "min_angle": 160,
                "max_angle": 195,
                "ok_message": "✓ Arms locked",
                "fix_message": "Straighten arms — hands under shoulders"
            }
        ]
    }
}


CONDITION_TO_POSES = {
    "back pain":            ["cobra", "downdog", "cat_cow"],
    "posture":              ["mountain", "cobra", "plank"],
    "leg strength":         ["warrior2", "chair", "tree"],
    "balance":              ["tree", "warrior2", "mountain"],
    "core strength":        ["plank", "chair"],
    "stress":               ["mountain", "downdog", "cobra"],
    "flexibility":          ["downdog", "cobra"],
    "focus":                ["tree", "mountain"],
    "hip mobility":         ["warrior2"],
    "spine flexibility":    ["cobra", "downdog"],
    "hamstrings":           ["downdog"],
    "full-body stretch":    ["downdog", "warrior2"],
}


def get_poses_for_condition(condition: str):
    """Return pose keys relevant to a health condition (case-insensitive fuzzy)."""
    cond = (condition or "").lower().strip()
    if not cond:
        return list(POSE_RULES.keys())[:4]
    matched = []
    for key, poses in CONDITION_TO_POSES.items():
        if key in cond or cond in key:
            for p in poses:
                if p in POSE_RULES and p not in matched:
                    matched.append(p)
    return matched or ["mountain", "tree", "warrior2", "downdog"]


def get_pose(key: str):
    return POSE_RULES.get(key)


def all_poses():
    return [{"key": k, **v} for k, v in POSE_RULES.items()]

# ============================================
# GENERIC MODES for exercises without specific pose rules
# ============================================

GENERIC_MODES = {
    # rep-counting exercises
    "squat_reps":       {"mode": "rep_counter", "landmark": "left_knee",     "axis": "y", "threshold": 0.15, "instruction": "Squat down and up", "min_visibility": 0.6, "hysteresis_frames": 3, "cooldown_ms": 500},
    "pushup_reps":      {"mode": "rep_counter", "landmark": "left_shoulder", "axis": "y", "threshold": 0.08, "instruction": "Bend elbows and press up", "min_visibility": 0.6, "hysteresis_frames": 3, "cooldown_ms": 500},
    "glute_bridge_reps":{"mode": "rep_counter", "landmark": "left_hip",      "axis": "y", "threshold": 0.10, "instruction": "Lift and lower hips", "min_visibility": 0.6, "hysteresis_frames": 3, "cooldown_ms": 500},

    # visibility-only (skeleton overlay + timer)
    "presence":         {"mode": "presence",    "instruction": "Stay in view — follow the on-screen instructions"},

    # breathing pace — track chest rise via shoulder movement
    "breathing":        {"mode": "breathing_pace", "landmark": "left_shoulder", "target_bpm": 6, "instruction": "Breathe slowly — follow the pace"},
}


# Map exercise titles / patterns to a generic mode
EXERCISE_MODE_MAP = {
    "squat":            "squat_reps",
    "push-up":          "pushup_reps",
    "push up":          "pushup_reps",
    "glute bridge":     "glute_bridge_reps",
    "anulom vilom":     "breathing",
    "box breathing":    "breathing",
    "bee breath":       "breathing",
    "bhramari":         "breathing",
    "4-7-8":            "breathing",
    # everything else → presence
}


def get_generic_mode(exercise_title: str) -> dict:
    """Return the generic camera mode for exercises without pose_key."""
    title_low = (exercise_title or "").lower()
    for pattern, mode_key in EXERCISE_MODE_MAP.items():
        if pattern in title_low:
            return {"key": mode_key, **GENERIC_MODES[mode_key]}
    return {"key": "presence", **GENERIC_MODES["presence"]}