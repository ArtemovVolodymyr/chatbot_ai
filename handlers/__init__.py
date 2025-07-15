#handlers/__init.py__
from .register import register, get_name, get_email, get_password
from .login import login, get_login_email, check_login
from .guest import guest

__all__ = [
    "register", "get_name", "get_email", "get_password",
    "login", "get_login_email", "check_login",
    "guest"
]
