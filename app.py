from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
import jwt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
CORS(app)

# Database setup
def get_db():
    db = sqlite3.connect('impactmatch.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    with get_db() as db:
        # Create users table
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL,
                name TEXT,
                city TEXT,
                age INTEGER,
                job TEXT,
                skills TEXT,
                user_values TEXT,
                availability TEXT,
                profile_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create associations table
        db.execute('''
            CREATE TABLE IF NOT EXISTS associations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                name TEXT,
                description TEXT,
                logo TEXT,
                verified BOOLEAN DEFAULT 0,
                impact_score REAL DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create missions table
        db.execute('''
            CREATE TABLE IF NOT EXISTS missions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                association_id INTEGER,
                title TEXT,
                emoji TEXT,
                description TEXT,
                impact_description TEXT,
                location TEXT,
                commitment TEXT,
                skills_required TEXT,
                tags TEXT,
                urgent BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (association_id) REFERENCES associations (id)
            )
        ''')
        
        # Insert sample data if database is empty
        user_count = db.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        if user_count == 0:
            print("📦 Inserting sample data...")
            
            # Create demo association user
            db.execute('''
                INSERT INTO users (email, password, user_type, name, city, job)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'greenpeace@demo.org', 
                hashlib.sha256('demo123'.encode()).hexdigest(), 
                'association', 
                'Greenpeace Maroc',
                'Casablanca',
                'ONG Environnementale'
            ))
            
            assoc_user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Create association profile
            db.execute('''
                INSERT INTO associations (user_id, name, description, verified, impact_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                assoc_user_id, 
                'Greenpeace Maroc', 
                'Protection de l\'environnement et sensibilisation climatique', 
                1, 
                92
            ))
            
            assoc_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Create demo citizen user
            db.execute('''
                INSERT INTO users (email, password, user_type, name, city, age, job, skills, user_values, availability, profile_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'amira@example.com',
                hashlib.sha256('demo123'.encode()).hexdigest(),
                'citizen',
                'Amira Benali',
                'Tunis',
                24,
                'Designer UX',
                json.dumps(['Design UX/UI', 'Communication', 'Social Media']),
                json.dumps(['🌱 Environnement', '📚 Éducation']),
                json.dumps(['Lundi soir', 'Mercredi soir', 'Télétravail OK']),
                85
            ))
            
            # Create sample missions
            missions = [
                (
                    'Chargé·e de communication digitale', 
                    '🌊', 
                    'Gérer les réseaux sociaux de la campagne "Océans Propres" pour toucher +10K personnes.',
                    'À distance', 
                    '8h/mois', 
                    0,
                    json.dumps([{'t': 'Social Media', 'c': 's'}, {'t': 'Rédaction', 'c': 's'}]),
                    json.dumps([{'t': 'Créativité', 'c': 'v'}, {'t': 'Autonomie', 'c': 'v'}])
                ),
                (
                    'Designer de contenus', 
                    '🎨', 
                    'Créer des visuels pour sensibiliser 5000 personnes aux droits de l\'enfant.',
                    'À distance', 
                    '5h/mois', 
                    1,
                    json.dumps([{'t': 'Design UX', 'c': 's'}, {'t': 'Photoshop', 'c': 's'}]),
                    json.dumps([{'t': 'Créativité', 'c': 'v'}, {'t': 'Empathie', 'c': 'v'}])
                ),
                (
                    'Mentor informatique pour ados', 
                    '💻', 
                    'Accompagner 8 jeunes (12-17 ans) dans l\'apprentissage du code',
                    'Tunis El Menzah', 
                    '4h/mois', 
                    1,
                    json.dumps([{'t': 'Dev Web', 'c': 's'}, {'t': 'Python', 'c': 's'}]),
                    json.dumps([{'t': 'Pédagogie', 'c': 'v'}, {'t': 'Patience', 'c': 'v'}])
                )
            ]
            
            for title, emoji, impact, location, commitment, urgent, skills, tags in missions:
                db.execute('''
                    INSERT INTO missions (association_id, title, emoji, impact_description, location, commitment, urgent, skills_required, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (assoc_id, title, emoji, impact, location, commitment, urgent, skills, tags))
            
            print("✅ Sample data inserted successfully!")

# Initialize database
init_db()

# ============= AI SERVICE =============
class AIService:
    @staticmethod
    def analyze_profile(profile_data):
        """Analyze citizen profile and return insights"""
        skills_count = len(profile_data.get('skills', []))
        values_count = len(profile_data.get('values', []))
        availability_count = len(profile_data.get('availability', []))
        
        # Calculate score
        score = min(100, 60 + skills_count * 5 + values_count * 3 + availability_count * 2)
        
        # Generate recommendations
        domains = []
        for v in profile_data.get('values', []):
            if 'environ' in v.lower():
                domains.append("🌱 Environnement")
            elif 'éduc' in v.lower() or 'educ' in v.lower():
                domains.append("📚 Éducation")
            elif 'santé' in v.lower():
                domains.append("⚕️ Santé")
            elif 'justice' in v.lower():
                domains.append("⚖️ Justice sociale")
            elif 'culture' in v.lower():
                domains.append("🎨 Culture")
            elif 'numéri' in v.lower():
                domains.append("💻 Numérique")
        
        # Remove duplicates and limit to 3
        domains = list(dict.fromkeys(domains))[:3]
        if not domains:
            domains = ["🌱 Environnement", "📚 Éducation", "💻 Numérique"][:min(3, skills_count)]
        
        # Soft skills based on job/age
        soft_skills = []
        if skills_count > 2:
            soft_skills.extend(["Communication", "Créativité"])
        if values_count > 1:
            soft_skills.append("Empathie")
        if availability_count > 2:
            soft_skills.append("Organisation")
        
        return {
            "score": score,
            "recommendations": domains,
            "soft_skills": soft_skills[:3],
            "advice": "Complète ton profil avec tes disponibilités pour des matchs encore plus précis !",
            "domains": domains
        }
    
    @staticmethod
    def generate_mission_from_text(text):
        """Generate mission from natural language"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['design', 'graphiste', 'visuel', 'créatif']):
            return {
                "title": "Designer créatif pour campagne impactante",
                "emoji": "🎨",
                "impact": "Créer des visuels qui sensibiliseront 5000 personnes à notre cause",
                "tags": [
                    {"t": "Design", "c": "mts"},
                    {"t": "Créativité", "c": "mtso"},
                    {"t": "5h/semaine", "c": "mtl"}
                ],
                "commitment": "Moyen - 5h/semaine en télétravail",
                "profiles": "32 profils",
                "attract": "87%",
                "matches": "8 matchs"
            }
        elif any(word in text_lower for word in ['communica', 'réseaux', 'social', 'media', 'content']):
            return {
                "title": "Community manager pour ONG",
                "emoji": "📱",
                "impact": "Animer les réseaux sociaux pour toucher 10K personnes",
                "tags": [
                    {"t": "Social Media", "c": "mts"},
                    {"t": "Rédaction", "c": "mtso"},
                    {"t": "3h/semaine", "c": "mtl"}
                ],
                "commitment": "Léger - 3h/semaine",
                "profiles": "45 profils",
                "attract": "92%",
                "matches": "12 matchs"
            }
        elif any(word in text_lower for word in ['code', 'dev', 'programmation', 'informatique']):
            return {
                "title": "Mentor en programmation pour jeunes",
                "emoji": "💻",
                "impact": "Former 20 jeunes aux bases du développement web",
                "tags": [
                    {"t": "Dev Web", "c": "mts"},
                    {"t": "Pédagogie", "c": "mtso"},
                    {"t": "4h/semaine", "c": "mtl"}
                ],
                "commitment": "Moyen - 4h/semaine",
                "profiles": "28 profils",
                "attract": "84%",
                "matches": "6 matchs"
            }
        elif any(word in text_lower for word in ['atelier', 'formation', 'enseigner', 'éduc']):
            return {
                "title": "Formateur·rice pour ateliers éducatifs",
                "emoji": "📚",
                "impact": "Animer des ateliers pour 30 enfants de quartiers défavorisés",
                "tags": [
                    {"t": "Formation", "c": "mts"},
                    {"t": "Pédagogie", "c": "mtso"},
                    {"t": "Week-end", "c": "mtl"}
                ],
                "commitment": "Occasionnel - 2 samedis/mois",
                "profiles": "38 profils",
                "attract": "89%",
                "matches": "10 matchs"
            }
        else:
            return {
                "title": "Mission de bénévolat",
                "emoji": "🤝",
                "impact": "Contribuer à une cause importante selon vos compétences",
                "tags": [
                    {"t": "Polyvalence", "c": "mtso"},
                    {"t": "Flexible", "c": "mtl"}
                ],
                "commitment": "Flexible - selon disponibilités",
                "profiles": "28 profils",
                "attract": "75%",
                "matches": "5 matchs"
            }

# ============= API ROUTES =============

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    hashed_pw = hashlib.sha256(data['password'].encode()).hexdigest()
    
    with get_db() as db:
        try:
            db.execute('''
                INSERT INTO users (email, password, user_type, name, city, age, job)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['email'], 
                hashed_pw, 
                data['userType'],
                data.get('name', ''),
                data.get('city', ''),
                data.get('age', 0),
                data.get('job', '')
            ))
            
            user_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # If association, create association profile
            if data['userType'] == 'association':
                db.execute('''
                    INSERT INTO associations (user_id, name)
                    VALUES (?, ?)
                ''', (user_id, data.get('name', '')))
            
            token = jwt.encode({
                'user_id': user_id, 
                'exp': datetime.utcnow() + timedelta(days=7)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'token': token, 
                'user': {
                    'id': user_id, 
                    'email': data['email'], 
                    'type': data['userType']
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    with get_db() as db:
        user = db.execute('SELECT * FROM users WHERE email = ?', (data['email'],)).fetchone()
        
        if user and user['password'] == hashlib.sha256(data['password'].encode()).hexdigest():
            token = jwt.encode({
                'user_id': user['id'], 
                'exp': datetime.utcnow() + timedelta(days=7)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'token': token, 
                'user': {
                    'id': user['id'], 
                    'email': user['email'], 
                    'type': user['user_type']
                }
            })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/profile/analyze', methods=['POST'])
def analyze_profile():
    data = request.json
    
    profile_data = {
        'name': data.get('name', ''),
        'city': data.get('city', ''),
        'age': data.get('age', 0),
        'job': data.get('job', ''),
        'skills': data.get('skills', []),
        'values': data.get('values', []),
        'availability': data.get('availability', [])
    }
    
    analysis = AIService.analyze_profile(profile_data)
    return jsonify(analysis)

@app.route('/api/missions', methods=['GET'])
def get_missions():
    with get_db() as db:
        missions = db.execute('''
            SELECT m.*, a.name as org_name, a.logo 
            FROM missions m
            LEFT JOIN associations a ON m.association_id = a.id
            WHERE m.status = 'active'
            ORDER BY m.created_at DESC
        ''').fetchall()
        
        result = []
        for m in missions:
            # Calculate random score for demo
            import random
            score = random.randint(75, 98)
            
            tags = json.loads(m['tags']) if m['tags'] else [
                {'t': 'Compétence', 'c': 's'},
                {'t': 'Bénévolat', 'c': 'v'},
                {'t': 'Flexible', 'c': 't'}
            ]
            
            result.append({
                'id': m['id'],
                'org': m['org_name'] or 'Association',
                'title': m['title'],
                'emoji': m['emoji'] or '🤝',
                'score': score,
                'impact': m['impact_description'],
                'tags': tags,
                'reasons': [
                    'Match IA détecté',
                    'Profil compatible',
                    'Disponibilités alignées'
                ][:random.randint(2, 3)],
                'meta': {
                    'loc': m['location'] or 'À distance',
                    'eng': m['commitment'] or 'Flexible',
                    'urgent': bool(m['urgent'])
                }
            })
        
        return jsonify(result)

@app.route('/api/ai/generate-mission', methods=['POST'])
def generate_mission():
    data = request.json
    user_input = data.get('text', '')
    mission = AIService.generate_mission_from_text(user_input)
    return jsonify(mission)

@app.route('/api/missions/create', methods=['POST'])
def create_mission():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'error': 'No token provided'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'error': 'Invalid token'}), 401
    
    mission_data = request.json
    
    with get_db() as db:
        # Get association id
        assoc = db.execute('SELECT id FROM associations WHERE user_id = ?', (user_id,)).fetchone()
        if not assoc:
            # Create association if doesn't exist
            user = db.execute('SELECT name FROM users WHERE id = ?', (user_id,)).fetchone()
            db.execute('INSERT INTO associations (user_id, name) VALUES (?, ?)', (user_id, user['name']))
            assoc_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        else:
            assoc_id = assoc['id']
        
        db.execute('''
            INSERT INTO missions (
                association_id, title, emoji, impact_description, 
                commitment, urgent, tags
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            assoc_id,
            mission_data.get('title', 'Nouvelle mission'),
            mission_data.get('emoji', '🤝'),
            mission_data.get('impact', ''),
            mission_data.get('commitment', 'Flexible'),
            0,
            json.dumps(mission_data.get('tags', []))
        ))
    
    return jsonify({'success': True})

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    # Return sample candidates
    candidates = [
        {
            'name': 'Amira Benali',
            'age': 24,
            'city': 'Tunis',
            'job': 'Designer UX',
            'emoji': '🙋',
            'score': 96,
            'mission': 'Campagne comm.',
            'skills': ['Design UX', 'Social Media'],
            'values': ['🌱 Environnement'],
            'sm': 95,
            'vm': 98,
            'am': 90,
            'why': 'Compétences alignées à 100%, valeur "Environnement" partagée.',
            'status': 'new'
        },
        {
            'name': 'Karim Ouhabi',
            'age': 28,
            'city': 'Casablanca',
            'job': 'Chef de projet',
            'emoji': '👨',
            'score': 88,
            'mission': 'Atelier écoles',
            'skills': ['Gestion projet', 'Formation'],
            'values': ['📚 Éducation'],
            'sm': 82,
            'vm': 94,
            'am': 88,
            'why': 'Expérience formation détectée, disponible week-ends.',
            'status': 'new'
        },
        {
            'name': 'Sara Mansouri',
            'age': 22,
            'city': 'Tunis',
            'job': 'Étudiante communication',
            'emoji': '👩',
            'score': 91,
            'mission': 'Design contenus',
            'skills': ['Communication', 'Créativité'],
            'values': ['🎨 Culture'],
            'sm': 89,
            'vm': 96,
            'am': 93,
            'why': 'Profil créatif fort, compétences visuelles.',
            'status': 'new'
        }
    ]
    return jsonify(candidates)

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    return jsonify({
        'active_missions': 7,
        'total_candidates': 24,
        'new_candidates': 4,
        'match_rate': 89,
        'people_impacted': 1240
    })

# Serve HTML frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 ImpactMatch API Server Starting...")
    print("=" * 50)
    print("📍 Server: http://localhost:5000")
    print("📦 Database: impactmatch.db (SQLite)")
    print("👤 Demo Association: greenpeace@demo.org / demo123")
    print("👤 Demo Citizen: amira@example.com / demo123")
    print("=" * 50)
    app.run(debug=True, port=5000)