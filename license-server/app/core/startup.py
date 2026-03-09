from fastapi import FastAPI
from ..database import get_db
from ..models.user import User
from ..models.role import Role
from ..security.security import hash_password


def init_app(app: FastAPI):

    @app.on_event("startup")
    def create_defaults():
        db = next(get_db())

        if not db.query(Role).filter(Role.name == "admin").first():
            print("Creando roles")
            db.add(Role(name="admin", description="Full access", features="All"))
            db.add(Role(name="users", description="Services Users", features="License"))
            db.add(Role(name="support", description="Administration", features="All"))
            db.commit()

        if not db.query(User).first():
            print("Creando usuario admin")
            role = db.query(Role).filter(Role.name == "admin").first()
            db.add(User(
                username="admin",
                email="admin@local",
                password_hash=hash_password("admin"),
                role=role
            ))
            db.commit()