from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from app.conn_session import db
from app.models.db import Users
import bcrypt


def helper_name(name):
    name = name.lower().strip()
    if len(name) < 5:
        return False

    special = "!#€%&/()=?^*_:;©@£$∞§|[]≈±´~™''æ…‚§¶°"
    num = "1234567890"

    if any(c in special for c in name):
        return False
    if any(c in num for c in name):
        return False
    return True


def helper_email(email):
    email = email.lower().strip()
    with db() as session:
        stmt = select(Users).where(Users.email == email)
        check_email = session.scalar(stmt)
        if check_email:
            return False
    return True


def helper_password(password):
    special = "!#€%&/()=?^*_:;©@£$∞§|[]≈±´~™''æ…‚§¶°"
    lower = "abcdefghijklmnopqrstuvwxyz"
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    num = "1234567890"
    password = password.strip()
    print(len(password))
    if len(password) < 4:
        return False
    if not any(c in special for c in password):
        return False
    if not any(c in lower for c in password):
        return False
    if not any(c in upper for c in password):
        return False
    if not any(c in num for c in password):
        return False
    return True


def hash_pw(password):
    if not helper_password(password):
        return False
    salt = bcrypt.gensalt()
    byts = password.encode('UTF-8')
    hashed_pw = bcrypt.hashpw(byts, salt)
    return hashed_pw.decode('UTF-8')


def register_user(name, email, password):
    if not helper_name(name):
        return False
    if not helper_email(email):
        return False
    password = hash_pw(password)
    if not password:
        return False

    try:
        with db() as session:
            stmt = insert(Users).values(name=name, email=email, password=password)
            session.execute(stmt)
    except IntegrityError:
        return False
    return True


def login_user(email, password):
    email = email.lower().strip()
    ids, mail = "", ""
    with db() as session:
        stmt = select(Users).where(Users.email == email)
        result = session.scalar(stmt)
        if result is None:
            return False
        if not bcrypt.checkpw(password.encode('UTF-8'), result.password.encode('UTF-8')):
            return False
        ids, mail = result.user_id, result.email
    return ids, mail
