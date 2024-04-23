from typing import Optional

from pydantic import BaseModel, Field


class RoleSpec(BaseModel):
    is_admin: bool = Field(alias='isAdmin', default=False)
    is_dev: bool = Field(alias='isDev', default=False)
    is_ops: bool = Field(alias='isOps', default=False)


class UserContactSpec(BaseModel):
    email: Optional[str] = None
    tel_office: Optional[str] = Field(alias='telOffice', default=None)
    tel_phone: Optional[str] = Field(alias='telPhone', default=None)


class UserSpec(BaseModel):
    contact: UserContactSpec = UserContactSpec()
    nickname: str = Field(alias='name', default='')


class User(BaseModel):
    box_name: Optional[str] = Field(alias='boxName', default=None)
    name: Optional[str] = Field(alias='userName', default=None)
    namespace: Optional[str] = None

    role: RoleSpec = RoleSpec()
    spec: UserSpec = Field(alias='user', default=UserSpec())
