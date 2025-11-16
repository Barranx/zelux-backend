from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import requests

from database import SessionLocal
from auth import get_password_hash
from models import User

import models, schemas
from database import Base, engine
from auth import (
    get_db,
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
    get_current_user_optional,
)

# ===========================================
#              DATABASE INIT
# ===========================================
Base.metadata.create_all(bind=engine)

def create_admin_user():
    db = SessionLocal()
    try:
        admin_email = "barranx.webservice@gmail.com"

        existing_admin = db.query(User).filter(User.email == admin_email).first()
        if existing_admin:
            print("👑 Admin già esistente:", admin_email)
            return

        admin_user = User(
            email=admin_email,
            full_name="Leonardo Barranco",
            hashed_password=get_password_hash("Zelux2025!"),  # password reale
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin creato con successo:")
        print("   Email:", admin_email)
        print("   Password:", "Zelux2025!")   # Mostri quella corretta!
    finally:
        db.close()

# Creazione admin automatico
create_admin_user()


# ===========================================
#                  APP SETUP
# ===========================================
app = FastAPI(title="Zelux Backend")

# CORS per frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # in produzione metti dominio reale
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1438899090065854637/c8RXenUo32ozO8SOuanvj-9istBbGl9xnzzOQAS4YVj8vqP5WbsStEZ_7_vnpEg1IvO-"


# ===========================================
#                ROUTE BASE
# ===========================================
@app.get("/")
def home():
    return {"status": "OK", "message": "Zelux Backend attivo 🔥"}


# ===========================================
#                REGISTER USER
# ===========================================
@app.post("/register", response_model=schemas.UserOut)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")

    hashed_pwd = get_password_hash(user_in.password)
    user = models.User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=hashed_pwd,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ===========================================
#                  LOGIN
# ===========================================
@app.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_in.email).first()

    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email o password errati")

    token = create_access_token({"sub": str(user.id), "is_admin": user.is_admin})
    return schemas.Token(access_token=token)


# ===========================================
#        CONTACT → SAVE + DISCORD
# ===========================================
@app.post("/send-contact")
def send_contact(
    data: schemas.ContactIn,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    # Save message in DB
    msg = models.Message(
        user_id=current_user.id if current_user else None,
        nome=data.nome,
        email=data.email,
        contenuto=data.messaggio,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    print(f"📨 Messaggio salvato nel DB: {msg.id} | {msg.nome} | {msg.email}")

    # Send to Discord
    payload = {
        "content": "**📩 Nuovo messaggio dal sito Zelux Studios**",
        "embeds": [
            {
                "title": "Dettagli del Contatto",
                "color": 16766720,
                "fields": [
                    {"name": "👤 Nome", "value": data.nome},
                    {"name": "📧 Email", "value": data.email},
                    {"name": "💬 Messaggio", "value": data.messaggio},
                ],
            }
        ],
    }

    try:
        r = requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        print("🔗 Webhook Discord inviato | Status:", r.status_code)
    except Exception as e:
        print("⚠ Errore invio Discord:", e)

    return {"success": True, "message_id": msg.id}


# ===========================================
#          ADMIN AREA – GET ALL MESSAGES
# ===========================================
@app.get("/admin/messages", response_model=List[schemas.MessageOut])
def get_all_messages(
    db: Session = Depends(get_db),
    admin: models.User = Depends(get_current_admin),
):
    messages = db.query(models.Message).order_by(models.Message.created_at.desc()).all()
    return messages
