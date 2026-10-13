from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Password = Annotated[str, StringConstraints(strip_whitespace=False, max_length=200)]

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Login(Input):
    username: str = Field(min_length=1, max_length=60)
    password: Password = Field(min_length=1)

class UserBody(Input):
    username: str = Field(min_length=2, max_length=60, pattern=r'^[A-Za-z0-9_.-]+$')
    name: str = Field(min_length=1, max_length=80)
    password: Password = Field(min_length=10)
    is_admin: bool = False

class ProjectBody(Input):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default='', max_length=4000)

class DocumentBody(Input):
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(default='', max_length=4000)

class MemberBody(Input):
    role: Literal['admin','analyst','reviewer','viewer']

class RequirementFields(Input):
    document_id: int | None = None
    parent_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=12000)
    source: str = Field(default='', max_length=2000)
    rationale: str = Field(default='', max_length=4000)
    type: Literal['functional','nonfunctional','constraint'] = 'functional'
    priority: Literal['must','should','could'] = 'must'
    owner_id: int | None = None
    acceptance: str = Field(default='', max_length=8000)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator('tags')
    @classmethod
    def valid_tags(cls, value):
        if any(not x.strip() or len(x) > 40 for x in value):
            raise ValueError('标签需为1至40字')
        return list(dict.fromkeys(x.strip() for x in value))

class RequirementCreate(RequirementFields):
    uid: str | None = Field(default=None, max_length=60, pattern=r'^[A-Za-z0-9_-]+$')

class RequirementUpdate(RequirementFields):
    expected_revision: int = Field(ge=1)

class RevisionBody(Input):
    expected_revision: int = Field(ge=1)

class SubmitBody(RevisionBody):
    reviewer_id: int

class DecisionBody(Input):
    decision: Literal['approved','rejected']
    comment: str = Field(default='', max_length=4000)

class LinkBody(Input):
    source_id: int
    target_id: int
    kind: Literal['refines','depends','conflicts']

class ArtifactBody(Input):
    kind: Literal['design','test']
    title: str = Field(min_length=1, max_length=200)
    reference: str = Field(default='', max_length=2000)
    result: Literal['not_run','passed','failed'] = 'not_run'
    requirement_ids: list[int] = Field(default_factory=list, max_length=500)

class ArtifactUpdate(ArtifactBody):
    expected_revision: int = Field(ge=1)

class BaselineBody(Input):
    name: str = Field(min_length=1, max_length=150)
    requirement_ids: list[int] = Field(default_factory=list, max_length=1000)

class ChangeBody(RevisionBody):
    title: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=4000)
    proposed: RequirementFields
