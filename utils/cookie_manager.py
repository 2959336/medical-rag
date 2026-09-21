import json
import os
import hashlib
from datetime import datetime, timedelta

class CookieManager:
    """基于文件的Cookie管理器，支持30天免登录"""
    
    COOKIE_DIR = os.path.join(os.path.dirname(__file__), ".cookies")
    
    @classmethod
    def _get_cookie_path(cls):
        os.makedirs(cls.COOKIE_DIR, exist_ok=True)
        return os.path.join(cls.COOKIE_DIR, "session.json")
    
    @classmethod
    def _encrypt(cls, data):
        """简单加密存储"""
        import base64
        return base64.b64encode(json.dumps(data).encode()).decode()
    
    @classmethod
    def _decrypt(cls, encrypted):
        """解密数据"""
        import base64
        try:
            return json.loads(base64.b64decode(encrypted.encode()).decode())
        except:
            return None
    
    @classmethod
    def save_login_cookie(cls, username, avatar, remember=True, days=30):
        """保存登录Cookie，remember为True时保存30天"""
        if not remember:
            return
        
        data = {
            "username": username,
            "avatar": avatar,
            "expires": (datetime.now() + timedelta(days=days)).isoformat(),
            "login_time": datetime.now().isoformat()
        }
        
        cookie_path = cls._get_cookie_path()
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cls._encrypt(data))
    
    @classmethod
    def load_login_cookie(cls):
        """加载登录Cookie，如果未过期返回用户信息，否则返回None"""
        cookie_path = cls._get_cookie_path()
        
        if not os.path.exists(cookie_path):
            return None
        
        try:
            with open(cookie_path, "r", encoding="utf-8") as f:
                encrypted = f.read()
            
            data = cls._decrypt(encrypted)
            if not data:
                return None
            
            expires = datetime.fromisoformat(data["expires"])
            if datetime.now() > expires:
                cls.clear_login_cookie()
                return None
            
            return {
                "username": data["username"],
                "avatar": data["avatar"]
            }
        except Exception:
            return None
    
    @classmethod
    def clear_login_cookie(cls):
        """清除登录Cookie"""
        cookie_path = cls._get_cookie_path()
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
    
    @classmethod
    def is_logged_in(cls):
        """检查是否已登录"""
        return cls.load_login_cookie() is not None


class UserManager:
    """用户注册管理"""
    
    USERS_FILE = os.path.join(os.path.dirname(__file__), ".users.json")
    
    @classmethod
    def _load_users(cls):
        if not os.path.exists(cls.USERS_FILE):
            return {}
        try:
            with open(cls.USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    
    @classmethod
    def _save_users(cls, users):
        os.makedirs(os.path.dirname(cls.USERS_FILE), exist_ok=True)
        with open(cls.USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def register(cls, username, password, avatar):
        """注册新用户，返回 (success, message)"""
        if not username or not password:
            return False, "用户名和密码不能为空"
        
        if len(username) < 3:
            return False, "用户名至少3个字符"
        
        if len(password) < 6:
            return False, "密码至少6个字符"
        
        users = cls._load_users()
        
        if username in users:
            return False, "用户名已存在"
        
        users[username] = {
            "password": password,
            "avatar": avatar,
            "created_at": datetime.now().isoformat()
        }
        
        cls._save_users(users)
        return True, "注册成功"
    
    @classmethod
    def verify(cls, username, password):
        """验证用户登录，返回 (success, avatar)"""
        users = cls._load_users()
        
        if username not in users:
            return False, None
        
        if users[username]["password"] != password:
            return False, None
        
        return True, users[username]["avatar"]
    
    @classmethod
    def user_exists(cls, username):
        """检查用户名是否存在"""
        users = cls._load_users()
        return username in users
    
    @classmethod
    def update_avatar(cls, username, avatar):
        """更新用户头像"""
        users = cls._load_users()
        if username in users:
            users[username]["avatar"] = avatar
            cls._save_users(users)
            return True
        return False
