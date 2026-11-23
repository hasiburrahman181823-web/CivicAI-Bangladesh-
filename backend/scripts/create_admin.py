"""Create an administrator with an operator-provided password."""
import argparse
import getpass

from argon2 import PasswordHasher
from pydantic import ValidationError
from sqlalchemy import select

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import User
from backend.app.schemas import ADMIN_PASSWORD_MINIMUM, Credentials

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    Base.metadata.create_all(engine)
    email=input("Admin email: ").strip().lower()
    password=getpass.getpass("Admin password: ")
    try:
        Credentials(email=email,password=password)
        if len(password)<ADMIN_PASSWORD_MINIMUM:
            raise ValueError()
    except (ValidationError,ValueError):
        raise SystemExit(f"Use a valid email and a password of {ADMIN_PASSWORD_MINIMUM}–128 characters.")
    hasher=PasswordHasher()
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if user:
            raise SystemExit("Account already exists.")
        if password!=getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords do not match.")
        db.add(User(email=email,password_hash=hasher.hash(password),role="admin"))
        db.commit()
    print("Administrator account created.")

if __name__=="__main__":
    main()
