from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import func,select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UserCreate,UserPublicResponse,UserUpdate,PostResponse,UserPrivateResponse,Token

from datetime import timedelta

from fastapi.security import OAuth2PasswordRequestForm

from auth import create_access_token, CurrenteUser, verify_password, hash_password
from config import settings



router=APIRouter()#"api/users it is past in prefix parameter when you import an include routers"

@router.post("",response_model=UserPrivateResponse,status_code=status.HTTP_201_CREATED)
async def post_user(user:UserCreate,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute( select(models.User).where(func.lower(models.User.user_name)==user.user_name.lower())) 
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User name already exist"

        )
    result=await db.execute(select(models.User).where(func.lower(models.User.email)==user.email.lower()))
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exist"
              )
    new_user=models.User(
        user_name=user.user_name,
        email=user.email.lower(),
        password_hash=hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],db:Annotated[AsyncSession, Depends(get_db)]):
    # Look up user by email (case-insensitive)
    # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(select(models.User).where(func.lower(models.User.email) == form_data.username.lower()))
    user = result.scalars().first()

    # Verify user exists and password is correct
    # Don't reveal which one failed (security best practice)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user id as subject
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )
    return Token(access_token=access_token, token_type="bearer")

## get_current_user
@router.get("/me", response_model=UserPrivateResponse)
async def get_current_user(current_user: CurrenteUser):
    return current_user

# add get all users
@router.get("/{user_id}",response_model=UserPublicResponse)
async def get_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id)) 
    user=result.scalars().first()
    if  user:
        return CurrenteUser
    
    raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
    
            )

@router.get("/{user_id}/posts",response_model=list[PostResponse])
async def get_user_posts(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id)) 
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
              detail="User not found"
                )
    result=await db.execute(select(models.Post).where(models.Post.user_id==user_id).options(selectinload(models.Post.author)).order_by(models.Post.date_posted.desc()))
    posts=result.scalars().all()
    return posts


# add put for the archetype
@router.patch("/{user_id}",response_model=UserPublicResponse,)
async def update_user_partial(user_id:int,user_update:UserUpdate,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException( 
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user because you are not the owner"
            )
    
    result = await db.execute(select(models.User).where(models.User.id==user_id)) 
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"

        )
    if user_update.user_name != None and user_update.user_name.lower() != user.user_name.lower():
         result = await db.execute(select(models.User).where(func.lower(models.User.user_name)==user_update.user_name.lower()) ) 
         existing_user=result.scalars().first()
         if existing_user:
             raise HTTPException(
                         status_code=status.HTTP_400_BAD_REQUEST,
                         detail="User name already exist"
             
                     )

    if user_update.email != None and user_update.email.lower() !=user.email.lower():
        result = await db.execute(select(models.User).where(func.lower(models.User.email)==user_update.email.lower()))
        existing_email=result.scalars().first()
        if existing_email:
            raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Email already registred"
              )
        
    if user_update.user_name is not None:
        user.user_name = user_update.user_name
    if user_update.email is not None:
        user.email = user_update.email.lower()
    if user_update.image_file is not None:
        user.image_file = user_update.image_file
    # update_data=user_update.model_dump(exclude_unset=True)
    # for field,value in update_data.items():
    #     setattr(user,field,value)

    await db.commit()
    await db.refresh(user)

    return user   

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id:int,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException( 
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user because you are not the owner"
            )
    
    result=await db.execute(select(models.User).where(models.User.id==user_id) ) 
    user=result.scalars().first()
    if  not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
                )
    await db.delete(user)  
    await db.commit()

