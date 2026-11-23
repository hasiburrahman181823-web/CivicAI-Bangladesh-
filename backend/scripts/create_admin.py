"""Create an administrator or enroll an existing administrator into app-based MFA."""
import argparse
import getpass

from argon2 import PasswordHasher
from pydantic import ValidationError
from sqlalchemy import delete, select

from backend.app.config import ADMIN_MFA_KEY, PRODUCTION
from backend.app.db import Base, SessionLocal, engine
from backend.app.mfa import encrypt_secret, matching_counter, new_secret
from backend.app.models import AdminMFA, LoginSession, User
from backend.app.schemas import Credentials

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enroll",action="store_true",help="Rotate MFA for an existing admin after identity verification")
    args=parser.parse_args()
    Base.metadata.create_all(engine)
    email=input("Admin email: ").strip().lower()
    password=getpass.getpass("Admin password: ")
    try:
        Credentials(email=email,password=password)
        if len(password)<12:
            raise ValueError()
    except (ValidationError,ValueError):
        raise SystemExit("Use a valid email and a password of 12–128 characters.")
    hasher=PasswordHasher()
    with SessionLocal() as db:
        user=db.scalar(select(User).where(User.email==email))
        if args.enroll:
            if not user or user.role!="admin":
                raise SystemExit("Administrator account not found.")
            hasher.verify(user.password_hash,password)
        else:
            if user:
                raise SystemExit("Account already exists.")
            if password!=getpass.getpass("Confirm password: "):
                raise SystemExit("Passwords do not match.")
            user=User(email=email,password_hash=hasher.hash(password),role="admin")
            db.add(user)
            db.flush()
        if PRODUCTION or ADMIN_MFA_KEY or args.enroll:
            secret=new_secret()
            encrypted=encrypt_secret(secret)
            print("Add this manual, time-based key in your authenticator app. Keep it private.")
            print(secret)
            counter=matching_counter(secret,getpass.getpass("Enter the generated 6-digit code: "))
            if counter is None:
                raise SystemExit("Enrollment code was invalid. No changes were saved.")
            db.merge(AdminMFA(user_id=user.id,secret_encrypted=encrypted,last_counter=counter))
        db.execute(delete(LoginSession).where(LoginSession.user_id==user.id))
        db.commit()
    print("Administrator setup saved. Use the next authenticator code if MFA is enabled.")

if __name__=="__main__":
    main()
