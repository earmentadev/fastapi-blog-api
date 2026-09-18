from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import UserCreate,UserResponse,UserUpdate,PostResponse

router=APIRouter()#"api/users it is past in prefix parameter when you import an include routers"
# add get all users
@router.get("/{user_id}",response_model=UserResponse)
async def get_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id)) 
    user=result.scalars().first()
    if  user:
        return user
    
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

@router.post("",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def post_user(user:UserCreate,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute( select(models.User).where(models.User.user_name==user.user_name)) 
    existing_user=result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User name already exist"

        )
    result=await db.execute(select(models.User).where(models.User.email==user.email))
    existing_email=result.scalars().first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exist"
              )
    new_user=models.User(
        user_name=user.user_name,
        email=user.email
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
# add put for the archetype
@router.patch("/{user_id}",response_model=UserResponse,)
async def update_user_partial(user_id:int,user_update:UserUpdate,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id)) 
    user=result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"

        )
    if user_update.user_name != None and user_update.user_name != user.user_name:
         result=db.execute(
                    select(models.User).where(models.User.user_name==user_update.user_name)
                ) 
         existing_user=result.scalars().first()
         if existing_user:
             raise HTTPException(
                         status_code=status.HTTP_400_BAD_REQUEST,
                         detail="User name already exist"
             
                     )

    if user_update.email != None and user_update.email !=user.email:
        result=await db.execute(select(models.User).where(models.User.email==user_update.email))
        existing_email=result.scalars().first()
        if existing_email:
            raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Email already registred"
              )
        
    if user_update.user_name is not None:
        user.user_name = user_update.user_name
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file
    # update_data=user_update.model_dump(exclude_unset=True)
    # for field,value in update_data.items():
    #     setattr(user,field,value)

    await db.commit()
    await db.refresh(user)

    return user   

@router.delete("/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delte_user(user_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
    result=await db.execute(select(models.User).where(models.User.id==user_id) ) 
    user=result.scalars().first()
    if  not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
                )
    await db.delete(user)  
    await db.commit()

    