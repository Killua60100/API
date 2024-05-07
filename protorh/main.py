import subprocess
import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, create_database
from pydantic import BaseModel
import bcrypt
import json
import os

app = FastAPI()

DATABASE_URL = "postgresql://killua60100:oklm@localhost:5432/postgresql" 

engine = create_engine(DATABASE_URL)

if not database_exists(engine.url):
    create_database(engine.url , template="template0")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ItemCreate(BaseModel):
    name: str
    price: float
    quantity: int

class Item(Base):
    __tablename__ = "items"  

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer)

class user(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    Email =Column(String)
    Password = Column(String)
    Firstname = Column(String)
    Lastname = Column(String)
    Birthday_date = Column(String)
    Address = Column(String)
    PostalCode = Column(Integer)
    Age = Column(Integer)
    Meta = json
    RegistrationDate = Column(String)
    Token = Column(String)
    Role= Column(String)


class UserCreate(BaseModel):
    Email : str
    Password: str
    Firstname: str
    Lastname: str
    Birthday_date: str
    Address: str
    PostalCode: int
    Age: str
    RegistrationDate : str
    Token: str
    Role: str

class UserUpdate(BaseModel):
    Firstname: str
    Lastname: str
    Roles: str
    Token: str
    Email: str
    BirthdayDate: str
    Address: str
    PostalCode: int
    Age: int

@app.get("/")
def index():
    return {"message": "Hello, world!"}

@app.get("/exit")
async def stop_server():
    subprocess.call(["pkill", "uvicorn"])
    return {"message": "stopped"}

@app.post("/items")
async def create_item(item: ItemCreate):
    with SessionLocal() as session:
        new_item = Item(
            name=item.name,
            price=item.price,
            quantity=item.quantity,
        )
        session.add(new_item)
        session.commit()
    return {"message": "Item created successfully!"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/user/create")
async def create_user(new_user: UserCreate,db: Session = Depends(get_db)):
    with engine.connect() as connection:
        result = connection.execute(text("INSERT INTO \"user\" (\"Email\", \"Password\", \"Firstname\", \"Lastname\", \"Birthday_date\", \"Address\", \"PostalCode\", \"Age\", \"RegistrationDate\", \"Token\", \"Role\") VALUES (:email, :password, :firstname, :lastname, :birthday_date, :address, :postal_code, :age, :registration_date, :token, :role) RETURNING id")),
        new_user = user(
            Email = new_user.Email,
            Password = new_user.Password,
            Firstname = new_user.Firstname,
            Lastname = new_user.Lastname,
            Birthday_date = new_user.Birthday_date,
            Address = new_user.Address,
            PostalCode = new_user.PostalCode,
            Age = new_user.Age,
            RegistrationDate = new_user.RegistrationDate,
            Token = new_user.Token,
            Role= new_user.Role
            )
        new_user_id = result.scalar()
    return {"user_id": new_user_id}
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/connect")
async def connect(email:str,password:str,db:Session = Depends(SessionLocal)):
    user = db.query(user).filter(user.firstname == email).first()
    if user is None:
        return {"l'utilisateur n'est pas trouvé"}
    if user.password == password:
        return {"connexion établie"}
    else:
        return {"mot de passe incorrect"} 

@app.get("/user/{id_user}")
async def recuperation(id_user:int, db:Session = Depends(get_db)):
    user = db.query(user).filter(user.id == id_user).first()
    if user is None:
         raise HTTPException(status_code=404, detail="l'utilisateur n'est pas trouvé")
    current_user = UserCreate
    if user.role == "administrateur":
        return {
             "firstname":current_user.firstname,
             "lastname": current_user.lastname,
            "birthday_date": current_user.birthday_date,
            "address": current_user.address,
            "postal_code": current_user.postal_code
         }
    else:
        return {
            "firstname": current_user.firstname,
            "lastname": current_user.lastname
        }

@app.post("/user/update")
async def update(id_user:int,user_update:UserUpdate, db:Session = Depends(SessionLocal)):
    user = db.query(user).filter(user.id == id_user).first()

    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if user.role == "administrateur":
        user_update.firstname = user.firstname
        user_update.lastname = user.lastname
        user_update.roles = user.roles
        user_update.token = user.token
        user_update.Email = user.email
        user_update.BirthdayDate = user.BirthdayDate
        user_update.Address = user.address
        user_update.PostalCode = user.PostalCode
        user_update.Age = user.Age
    else:
        user_update.Email = user.email
        user_update.BirthdayDate = user.BirthdayDate
        user_update.Address = user.address
        user_update.PostalCode = user.PostalCode
        user_update.Age = user.Age

        db.commit()
        db.refresh(user)
        return user

@app.post("/user/password")
async def password(email:str,password:str,new_password:str,repeat_new_password:str, db:Session = Depends(SessionLocal)):
    user = db.query(user).filter(user.email == email).first()
    if user is None:
        return {"utilisateur non trouvé"}
    
    if password != user.password:
        return {"mot de passe incorrect"}
    if new_password != repeat_new_password:
        return {"les nouveaux mots de passe ne correspondent pas"}
    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)

    