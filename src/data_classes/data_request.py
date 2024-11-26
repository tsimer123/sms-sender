from pydantic import BaseModel, ConfigDict


class GetResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    data: str | None = None
    error: list | None = None
