from pydantic import BaseModel, Field


class RoleSpec(BaseModel):
    is_admin: bool = Field(alias='isAdmin', default=False)
    is_dev: bool = Field(alias='isDev', default=False)
    is_ops: bool = Field(alias='isOps', default=False)


class UserContactSpec(BaseModel):
    email: str | None = None
    tel_office: str | None = Field(alias='telOffice', default=None)
    tel_phone: str | None = Field(alias='telPhone', default=None)


class UserSpec(BaseModel):
    contact: UserContactSpec = UserContactSpec()
    nickname: str = Field(alias='name', default='')


class User(BaseModel):
    box_name: str | None = Field(alias='boxName', default=None)
    name: str | None = Field(alias='userName', default=None)
    namespace: str | None = None

    role: RoleSpec = RoleSpec()
    spec: UserSpec = Field(alias='user', default=UserSpec())
