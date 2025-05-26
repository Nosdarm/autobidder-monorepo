from pydantic import BaseModel
from typing import Dict  # Any removed


class TemplateBase(BaseModel):
    name: str
    # value: Dict[str, Any] # Using Any for Dict values as structure is not
    # strictly defined yet
    value: Dict  # Per instruction, keeping as Dict for now
    owner_id: str


class Template(TemplateBase):
    # In case we need to distinguish between input and output,
    # but for now, it's the same as TemplateBase.
    # If these were ORM models, we'd add:
    # model_config = ConfigDict(from_attributes=True)
    pass

# If there were create/update specific schemas, they would go here.
# For example:
# class TemplateCreate(TemplateBase):
#     pass

# class TemplateUpdate(BaseModel):
#     name: Optional[str] = None
#     value: Optional[Dict[str, Any]] = None

# For now, the existing Template model in the router is used for creation
# (request body). We'll use Template for response where a full template
# is returned.
