"""
Database models for the Llama Chat application
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    PREMIUM = "premium"
    BASIC = "basic"

class User(UserMixin, db.Model):
    """User model with profile information and role management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.BASIC, nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, username, password, name, email=None, role=UserRole.BASIC):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.name = name
        self.email = email
        self.role = role
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def set_password(self, password):
        """Set a new password hash"""
        self.password_hash = generate_password_hash(password)
    
    def has_role(self, role):
        """Check if user has a specific role or higher"""
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MODERATOR: 3,
            UserRole.PREMIUM: 2,
            UserRole.BASIC: 1
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    def is_moderator(self):
        """Check if user is a moderator or admin"""
        return self.has_role(UserRole.MODERATOR)
    
    def is_premium(self):
        """Check if user is premium or higher"""
        return self.has_role(UserRole.PREMIUM)
    
    def update_last_login(self):
        """Update the last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def total_messages(self):
        """Get total number of messages across all sessions"""
        total = 0
        for session in self.chat_sessions:
            total += len(session.messages)
        return total
    
    def days_since_joined(self):
        """Get number of days since user joined"""
        if self.created_at:
            delta = datetime.utcnow() - self.created_at
            return delta.days
        return 0
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'avatar_url': self.avatar_url,
            'bio': self.bio,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class ChatSession(db.Model):
    """Chat session model to group messages"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    model_used = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan', order_by='Message.created_at')
    
    def __init__(self, user_id, model_used, title=None):
        self.user_id = user_id
        self.model_used = model_used
        self.title = title
    
    def get_message_count(self):
        """Get the number of messages in this session"""
        return len(self.messages)
    
    def get_last_message(self):
        """Get the last message in this session"""
        return self.messages[-1] if self.messages else None
    
    def generate_title_from_content(self):
        """Generate a title based on the conversation content"""
        if not self.messages:
            return "New Chat"
        
        # Get the first few user messages to understand the topic
        user_messages = [msg.content for msg in self.messages if msg.role == 'user'][:3]
        if not user_messages:
            return "New Chat"
        
        # Combine the first few messages
        combined_content = " ".join(user_messages)
        
        # Simple title generation logic
        words = combined_content.split()
        if len(words) <= 5:
            # Short message, use as is
            title = combined_content[:50].strip()
        else:
            # Longer message, extract key words
            # Remove common words and punctuation
            common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may', 'might', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
            
            # Filter out common words and short words
            key_words = [word.lower().strip('.,!?;:') for word in words 
                        if word.lower().strip('.,!?;:') not in common_words 
                        and len(word.strip('.,!?;:')) > 2]
            
            if key_words:
                # Take first 3-4 key words
                title = " ".join(key_words[:4]).title()
            else:
                # Fallback to first few words
                title = " ".join(words[:4]).title()
        
        # Clean up the title
        title = title.strip()
        if len(title) > 40:
            title = title[:37] + "..."
        
        return title if title else "New Chat"
    
    def update_title(self):
        """Update the session title based on content"""
        self.title = self.generate_title_from_content()
        return self.title
    
    def get_formatted_date(self):
        """Get a clean formatted date for display"""
        now = datetime.utcnow()
        created_date = self.created_at
        
        if created_date.date() == now.date():
            return "Today"
        elif created_date.date() == (now - timedelta(days=1)).date():
            return "Yesterday"
        else:
            return created_date.strftime("%b %d")  # e.g., "Jul 13"
    
    def formatted_date(self):
        """Alias for get_formatted_date for template compatibility"""
        return self.get_formatted_date()
    
    def message_count(self):
        """Alias for get_message_count for template compatibility"""
        return self.get_message_count()
    
    def to_dict(self):
        """Convert session to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'model_used': self.model_used,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active,
            'message_count': self.get_message_count(),
            'last_message': self.get_last_message().to_dict() if self.get_last_message() else None,
            'formatted_date': self.get_formatted_date()
        }

class Message(db.Model):
    """Message model for storing chat messages"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tokens_used = db.Column(db.Integer, nullable=True)
    response_time = db.Column(db.Float, nullable=True)  # Response time in seconds
    
    def __init__(self, session_id, content, role, tokens_used=None, response_time=None):
        self.session_id = session_id
        self.content = content
        self.role = role
        self.tokens_used = tokens_used
        self.response_time = response_time
    
    def to_dict(self):
        """Convert message to dictionary for API responses"""
        return {
            'id': self.id,
            'content': self.content,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'tokens_used': self.tokens_used,
            'response_time': self.response_time
        }

class SystemSettings(db.Model):
    """System settings model for application configuration"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, key, value, description=None):
        self.key = key
        self.value = value
        self.description = description

# Database initialization function
def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if no users exist
        if not User.query.first():
            admin_user = User(
                username='admin',
                password='admin123',
                name='Administrator',
                email='admin@chatbot.com',
                role=UserRole.ADMIN
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Created default admin user: admin/admin123")
        
        # Create default system settings
        default_settings = [
            ('max_messages_per_session', '100', 'Maximum messages per chat session'),
            ('default_model', 'gemma3:4b-it-qat', 'Default AI model to use'),
            ('session_timeout_hours', '24', 'Session timeout in hours'),
            ('enable_user_registration', 'true', 'Allow new user registration'),
            ('max_sessions_per_user', '50', 'Maximum chat sessions per user'),
        ]
        
        for key, value, description in default_settings:
            if not SystemSettings.query.filter_by(key=key).first():
                setting = SystemSettings(key=key, value=value, description=description)
                db.session.add(setting)
        
        db.session.commit()
        print("Database initialized successfully!") 