from pydantic import BaseModel, ConfigDict


class TaskIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phone_number: str
    command: str


class TaskSms(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    ip: str
    login: str
    passw: str
