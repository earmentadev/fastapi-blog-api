from datetime import UTC,datetime,timedelta

import jwt
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from config import settings

from typing import Annotated
from fastapi import Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import models
from database import get_db

password_hash = PasswordHash.recommended()#argon2

oauth2_schema=OAuth2PasswordBearer(tokenUrl="api/users/token") #extract form the hader the token

def hash_password(password:str) -> str:
    return password_hash.hash(password)

def verify_password(palin_password:str,hashed_password:str) -> bool: # we are using hash because hashin is ireversible encrypt is reversible
    return password_hash.verify(palin_password,hashed_password)

def create_access_token(data:dict,expires_delta:timedelta | None = None) -> str:
    """Create a Json Web Token access token"""
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(UTC) + expires_delta
    else:
        expire=datetime.now(UTC) + timedelta(minutes=settings.acces_toke_expire_minutes)

    to_encode.update({"exp":expire})
    encode_jwt=jwt.encode(to_encode,settings.secret_key.get_secret_value(),algorithm=settings.algorithm)

    return encode_jwt

def verify_access_token(token:str) -> str | None:
    """Verify a Json Web Token access token and return the user (user_id) if is a valid jwt"""
    try:
         payload = jwt.decode(token,settings.secret_key.get_secret_value(),algorithms=settings.algorithm,options={"require":["exp","sub"]})
    except jwt.InvalidTokenError:
        return None
    else:
        return payload.get("sub")
    
async def get_current_user(token:Annotated[str, Depends(oauth2_schema)], db: Annotated [AsyncSession, Depends(get_db)]) -> models.User:
    user_id= verify_access_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expire Token",
            headers={"WWW-Authenticate":"Bearer"}
        )
    try:
        user_id_int=int(user_id)
    except:
        raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expire Token",
                    headers={"WWW-Authenticate":"Bearer"}
                )
    result = await db.excute(select(models.User).where(models.User-id==user_id_int))
    user=result.scalars().first()
    if not user:
        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="IUser not found",
                            headers={"WWW-Authenticate":"Bearer"}
                        )
    return user

CurrenteUser = Annotated[models.User,Depends(get_current_user)]# Type alias from annoted to no repeat code


    