from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime

class UserBase(BaseModel):
    user_name:str=Field(min_length=1, max_length=50)
    email:EmailStr=Field( max_length=120)

    

class UserCreate(UserBase):
    password:str=Field(min_length=8)
    


class UserPublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # this allow to use atributes from the database model like user.user_name
    id:int
    user_name:str
    image_file:str|None
    image_path:str

class UserPrivateResponse(UserPublicResponse):
    email:EmailStr

class UserUpdate(BaseModel):
    user_name:str|None=Field(default=None,min_length=1, max_length=50)
    email:EmailStr|None=Field(default=None, max_length=120)

class Token(BaseModel):
    access_token:str
    token_type:str

class PostBase(BaseModel):
    title:str=Field(min_length=1, max_length=100)
    content:str=Field(min_length=1)

class PostUpdate(BaseModel):
    title:str|None=Field(default=None, min_length=1, max_length=100)
    content:str|None=Field(default=None, min_length=1)

class PostCreate(PostBase):
    pass


class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)
    id:int
    user_id:int
    date_posted:datetime
    author:UserPublicResponse

class PaginatedPostResponse(BaseModel):
    posts: list[PostResponse]
    total:int
    skip:int
    limit: int
    has_more:bool
