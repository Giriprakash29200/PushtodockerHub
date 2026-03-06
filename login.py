from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.oauth2 import OAuth2
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv
from passlib.context import CryptContext
from database import SessionLocal, engine
import models
import os

# ---------------- CONFIG ----------------

load_dotenv("login.env")

SECRET_KEY = os.getenv("LOGIN_SECRETKEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
token_blacklist = set()

# ---------------- DATABASE ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------- CUSTOM OAUTH (NO CLIENT ID/SECRET) ----------------

class OAuth2PasswordOnly(OAuth2):
    def __init__(self, tokenUrl: str):
        flows = OAuthFlowsModel(
            password={"tokenUrl": tokenUrl, "scopes": {}}
        )
        super().__init__(flows=flows)

    async def __call__(self, request: Request):
        authorization = request.headers.get("Authorization")
        scheme, token = get_authorization_scheme_param(authorization)

        if not authorization or scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Not authenticated")

        return token

oauth2_scheme = OAuth2PasswordOnly(tokenUrl="/login")

# ---------------- PASSWORD ----------------

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ---------------- JWT ----------------

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": username,
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme)):

    if token in token_blacklist:
        raise HTTPException(status_code=401, detail="Token has been logged out")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return username

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# ---------------- ROUTES ----------------

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    student = db.query(models.Student).filter(
        models.Student.register_number == form_data.username
    ).first()

    if not student or not verify_password(form_data.password, student.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_token(student.name)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/secure")
def secure_data(username: str = Depends(verify_token)):
    return {
        "message": f"Hello {username}",
        "status": "Access granted"
    }


@app.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    username: str = Depends(verify_token)
):
    token_blacklist.add(token)

    return {
        "message": f"User '{username}' logged out successfully"
    }