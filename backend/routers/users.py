from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import aiosqlite

from backend.database import get_db
from backend import crud
from backend.schemas import UserCreate, UserLogin, Token, UserOut
from backend.deps import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/token", response_model=Token)
async def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Swagger sends "username" — we treat it as email
    user = await crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Wrong email or password")

    token = create_access_token(str(user["id"]))
    return {"access_token": token, "token_type": "bearer"}


@router.post("/signup", response_model=UserOut)
async def signup(payload: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    try:
        user = await crud.create_user(db, payload.email, hash_password(payload.password))
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: aiosqlite.Connection = Depends(get_db)):
    user = await crud.get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong email or password")

    token = create_access_token(str(user["id"]))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return user
