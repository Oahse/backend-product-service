from fastapi import APIRouter, Depends, HTTPException, status,BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from core.utils.response import Response
from models.user import UserRole, User
from services.user import UserService  # assuming your UserService is here
from schemas.user import UserCreate, UserRead, UserUpdate,UserLogin,ChangePasswordRequest  # your Pydantic schemas
from core.utils.messages.email import send_email

router = APIRouter(prefix='/api/v1/users', tags=["Users"])



@router.post("/")
async def create_user(user_in: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.create_user(
        firstname=user_in.firstname,
        lastname=user_in.lastname,
        email=user_in.email,
        password=user_in.password,
        role=UserRole(user_in.role),
        age=user_in.age,
        gender=user_in.gender,
        phone_number=user_in.phone_number,
        phone_number_pre=user_in.phone_number_pre,
        picture=user_in.picture,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    # send email to mail
    # token will also expire in 24hrs
    activation_link = "https://yourapp.com/activate?token=abc123"
    
    # send email in background (won't block the response)
    background_tasks.add_task(send_email, 
                              to_email="user@example.com", 
                              activation_link=activation_link,
                              from_email="youremail@gmail.com",
                              from_password="your-app-password")
    
    return Response(data=user.to_dict(), message='User created successfully', code=201)

@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.get_user_by_id(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # print(user.activation_token,'.activation_token----')
    return Response(data=user.to_dict(), message='User fetched successfully')

@router.put("/{user_id}")
async def update_user(user_id: str, user_in: UserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    update_data = user_in.dict(exclude_unset=True)
    user, err = await service.update_user(user_id, **update_data)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user.to_dict(), message='User updated successfully')

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success, err = await service.delete_user(user_id)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not success:
        raise HTTPException(status_code=404, detail="User not found or could not be deleted")
    return Response(data=True, message='User deleted successfully')

@router.get("/")
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    users, err = await service.list_users(skip=skip, limit=limit)
    if err:
        raise HTTPException(status_code=400, detail=err)
    return Response(data=users, message='Users fetched successfully')


@router.post("/login")
async def login_user(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.login(credentials.email, credentials.password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Here you can generate and attach JWT tokens, etc.
    return Response(data=user.to_dict(), message='User loggedin successfully')

@router.get("/{token}/activate")
async def activate_user(token: str, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    user, err = await service.activate(token)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return Response(data=user.to_dict(), message='User activated successfully')

@router.post("/{user_id}/change-password")
async def change_password(user_id: str, request: ChangePasswordRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    success, err = await service.change_password(user_id, request.old_password, request.new_password)
    if err:
        raise HTTPException(status_code=400, detail=err)
    if not success:
        raise HTTPException(status_code=401, detail="Old password is incorrect or user not found")
    return Response(data=True)
