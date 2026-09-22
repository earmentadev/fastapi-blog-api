from typing import Annotated

from fastapi import APIRouter,Depends,HTTPException,status,Query
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import models
from database import get_db
from schemas import PostCreate,PostUpdate,PostResponse,PaginatedPostResponse
from auth import CurrenteUser

from config import settings

router=APIRouter()#"api/posts it is past in prefix parameter when you import an include routers"

@router.get("/{post_id}",response_model=PostResponse)
async def get_post(post_id:int,db:Annotated[AsyncSession, Depends(get_db)]):
     result = await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
     post=result.scalars().first()
     if post:
        return post
     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")


@router.get("",response_model=PaginatedPostResponse)
async def get_posts(db:Annotated[AsyncSession, Depends(get_db)],skip:Annotated[int,Query(ge=0)]=0,limit:Annotated[int,Query(ge=1,le=100)]=settings.posts_per_page):
     #skip and limit is felxible than page per page
     count_result = await db.execute(select(func.count()).select_from(models.Post))
     total=count_result.scalar() or 0
     result = await db.execute(select(models.Post)
                             .options(selectinload(models.Post.author))
                             .order_by(models.Post.date_posted.desc())
                             .offset(skip)
                             .limit(limit))
     posts=result.scalars().all()
     has_more = skip + len(posts) < total
     # skip = 5 ->  ignore the first 5
     # limit = 10 -> give the next  10
     return PaginatedPostResponse(
          posts=[PostResponse.model_validate(post) for post in posts],
          total=total,
          skip=skip,
          limit=limit,
          has_more=has_more
     )

@router.post("",response_model=PostResponse,status_code=status.HTTP_201_CREATED)
async def post_post(post:PostCreate,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
     new_post= models.Post(
         title=post.title,
         content=post.content,
         user_id=current_user.id
         )
     
     db.add(new_post)
     await db.commit()
     await db.refresh(new_post,attribute_names=["author"]) #load the relation to author -- user 

     return new_post


@router.put("{post_id}",response_model=PostResponse)
async def update_post_full(post_id:int,post_data:PostCreate,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
     result=await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
     post=result.scalars().first()
     if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

     
     if post.user_id != current_user.id:
         raise HTTPException( 
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Not authorized to update this post because you are not the owner"
         )
     post.title=post_data.title
     post.content=post_data.content
     post.user_id=current_user.id

     await db.commit()
     await db.refresh(post,attribute_names=["author"])

     return post

@router.patch("/{post_id}",response_model=PostResponse)
async def update_post_partial(post_id:int,post_data:PostUpdate,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
     result=await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
     post=result.scalars().first()
     if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
     
     if post.user_id != current_user.id:
              raise HTTPException( 
                  status_code=status.HTTP_403_FORBIDDEN,
                  detail="Not authorized to update this post because you are not the owner"
              )

     update_data=post_data.model_dump(exclude_unset=True)
     for field,value in update_data.items():
         setattr(post,field,value)
         
     await db.commit()
     await db.refresh(post,attribute_names=["author"])

     return post

@router.delete("/{post_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id:int,current_user:CurrenteUser,db:Annotated[AsyncSession, Depends(get_db)]):
     result=await db.execute(select(models.Post).where(models.Post.id==post_id).options(selectinload(models.Post.author)))
     post=result.scalars().first()
     if not post:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")

     if post.user_id != current_user.id:
                   raise HTTPException( 
                       status_code=status.HTTP_403_FORBIDDEN,
                       detail="Not authorized to delete this post because you are not the owner"
                   )

     await db.delete(post)    
     await db.commit()