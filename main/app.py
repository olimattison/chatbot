"""
chatbot/main/app.py

Enhanced Llama Chat application with database integration, user management, and chat history.
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import json
from datetime import datetime, timedelta
import time
import os

# Import our models
from models import db, User, ChatSession, Message, SystemSettings, UserRole, init_db

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production!

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Helper functions
def get_setting(key, default=None):
    """Get a system setting value"""
    setting = SystemSettings.query.filter_by(key=key).first()
    return setting.value if setting else default

def require_role(role):
    """Decorator to require specific user role"""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if not current_user.has_role(role):
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        # Preserve the original function name to avoid conflicts
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

def get_available_models():
    """Get list of available models from Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = []
            for model in data.get('models', []):
                models.append({
                    'name': model['name'],
                    'size': model.get('size', 0),
                    'modified_at': model.get('modified_at', '')
                })
            return models
        else:
            # Fallback to default models if Ollama is not available
            return [
                {'name': 'No Models Available!', 'size': 0},
            ]
    except Exception as e:
        print(f"Error getting models from Ollama: {e}")
        # Fallback to default models
        return [
            {'name': 'No Models Available!', 'size': 0},
        ]

# Routes
@app.route('/')
@login_required
def index():
    """Main chat interface"""
    # Get user's active session or create new one
    active_session = ChatSession.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).first()
    
    if not active_session:
        default_model = get_setting('default_model', 'gemma3:4b-it-qat')
        active_session = ChatSession(
            user_id=current_user.id,
            model_used=default_model
        )
        db.session.add(active_session)
        db.session.commit()
    
    # Get recent sessions for sidebar
    recent_sessions = ChatSession.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatSession.updated_at.desc()).limit(10).all()
    
    # Get available models from Ollama
    available_models = get_available_models()
    
    return render_template('index.html', active_session=active_session, recent_sessions=recent_sessions, available_models=available_models)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            user.update_last_login()
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if registration is enabled
    if get_setting('enable_user_registration', 'true').lower() != 'true':
        flash('User registration is currently disabled.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        name = request.form.get('name', username)
        email = request.form.get('email')
        
        # Validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
        elif email and User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
        else:
            user = User(
                username=username,
                password=password,
                name=name,
                email=email,
                role=UserRole.BASIC
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Handle chat messages with session management"""
    user_input = request.json.get("prompt", "")
    model = request.json.get("model", get_setting('default_model', 'gemma3:4b-it-qat'))
    session_id = request.json.get("session_id")
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    # Get or create chat session
    if session_id:
        chat_session = ChatSession.query.filter_by(
            id=session_id, 
            user_id=current_user.id
        ).first()
    else:
        # Create new session
        chat_session = ChatSession(
            user_id=current_user.id,
            model_used=model
        )
        db.session.add(chat_session)
        db.session.commit()
    
    if not chat_session:
        return jsonify({"error": "Invalid session"}), 400
    
    # Check message limit
    max_messages = int(get_setting('max_messages_per_session', '100'))
    if len(chat_session.messages) >= max_messages:
        return jsonify({"error": f"Session limit reached ({max_messages} messages)"}), 400
    
    # Save user message
    user_message = Message(
        session_id=chat_session.id,
        content=user_input,
        role='user'
    )
    db.session.add(user_message)
    db.session.commit()
    
    # Update session title if this is the first message or title is still default
    if not chat_session.title or chat_session.title == "New Chat":
        chat_session.update_title()
        db.session.commit()
    
    # Get AI response
    start_time = time.time()
    try:
        payload = {
            "model": model,
            "prompt": user_input,
            "stream": True
        }
        
        response = requests.post("http://localhost:11434/api/generate", json=payload, stream=True)
        response.raise_for_status()
        
        reply = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode('utf-8'))
                reply += data.get("response", "")
        
        response_time = time.time() - start_time
        
        # Save AI response
        ai_message = Message(
            session_id=chat_session.id,
            content=reply,
            role='assistant',
            response_time=response_time
        )
        db.session.add(ai_message)
        db.session.commit()
        
        return jsonify({
            "response": reply,
            "session_id": chat_session.id,
            "response_time": response_time
        })
        
    except Exception as e:
        return jsonify({"error": f"Error contacting Ollama: {str(e)}"}), 500

@app.route('/sessions')
@login_required
def sessions():
    """User's chat sessions"""
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return render_template('sessions.html', sessions=sessions)

@app.route('/session/<int:session_id>')
@login_required
def view_session(session_id):
    """View a specific chat session"""
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        flash('Session not found', 'error')
        return redirect(url_for('sessions'))
    
    return render_template('session_view.html', session=session)

@app.route('/api/sessions')
@login_required
def api_sessions():
    """API endpoint for user sessions"""
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return jsonify([session.to_dict() for session in sessions])

@app.route('/api/session/<int:session_id>/messages')
@login_required
def api_session_messages(session_id):
    """API endpoint for session messages"""
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.created_at).all()
    return jsonify({
        "success": True,
        "messages": [message.to_dict() for message in messages]
    })

@app.route('/api/models')
@login_required
def api_models():
    """API endpoint for available models"""
    models = get_available_models()
    return jsonify({"models": models})

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        bio = request.form.get('bio')
        
        if name:
            current_user.name = name
        if email:
            current_user.email = email
        if bio is not None:
            current_user.bio = bio
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('edit_profile.html')

# Admin routes
@app.route('/admin')
@login_required
@require_role(UserRole.ADMIN)
def admin_dashboard():
    """Admin dashboard"""
    users = User.query.all()
    sessions = ChatSession.query.all()
    messages = Message.query.all()
    
    stats = {
        'total_users': len(users),
        'total_sessions': len(sessions),
        'total_messages': len(messages),
        'active_users': len([u for u in users if u.is_active])
    }
    
    return render_template('admin/dashboard.html', stats=stats, users=users)

@app.route('/admin/users')
@login_required
@require_role(UserRole.ADMIN)
def admin_users():
    """User management page"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@require_role(UserRole.ADMIN)
def admin_edit_user(user_id):
    """Edit user (admin only)"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form.get('name', user.name)
        user.email = request.form.get('email', user.email)
        user.role = UserRole(request.form.get('role', user.role.value))
        user.is_active = request.form.get('is_active') == 'on'
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user, roles=UserRole)

@app.route('/admin/settings')
@login_required
@require_role(UserRole.ADMIN)
def admin_settings():
    """System settings page"""
    settings = SystemSettings.query.all()
    return render_template('admin/settings.html', settings=settings)

@app.route('/admin/settings/<key>', methods=['POST'])
@login_required
@require_role(UserRole.ADMIN)
def admin_update_setting(key):
    """Update system setting"""
    setting = SystemSettings.query.filter_by(key=key).first()
    if setting:
        setting.value = request.form.get('value', setting.value)
        db.session.commit()
        flash('Setting updated successfully!', 'success')
    
    return redirect(url_for('admin_settings'))

if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')

