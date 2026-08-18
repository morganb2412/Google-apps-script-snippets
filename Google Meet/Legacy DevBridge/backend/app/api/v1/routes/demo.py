from fastapi import APIRouter

from app.demo.models import (
    AgentRequest,
    AgentResult,
    BranchRequest,
    CommitRequest,
    ConnectDemoRequest,
    DemoFile,
    DemoWorkspace,
)
from app.demo.service import DemoWorkspaceService

router = APIRouter(prefix="/demo", tags=["demo"])
_service = DemoWorkspaceService()


@router.get("/workspace", response_model=DemoWorkspace)
async def workspace() -> DemoWorkspace:
    return _service.get()


@router.get("/files", response_model=list[DemoFile])
async def files() -> list[DemoFile]:
    return _service.files()


@router.post("/connect", response_model=DemoWorkspace)
async def connect(request: ConnectDemoRequest) -> DemoWorkspace:
    return _service.connect(request.owner, request.repository)


@router.post("/branches", response_model=DemoWorkspace)
async def create_branch(request: BranchRequest) -> DemoWorkspace:
    return _service.create_branch(request.name)


@router.post("/commits", response_model=DemoWorkspace)
async def commit(request: CommitRequest) -> DemoWorkspace:
    return _service.commit(request.message)


@router.post("/pull-requests", response_model=DemoWorkspace)
async def pull_request() -> DemoWorkspace:
    return _service.create_pull_request()


@router.post("/agent/plan", response_model=AgentResult)
async def plan(request: AgentRequest) -> AgentResult:
    return _service.plan(request.request)


@router.post("/agent/review", response_model=AgentResult)
async def review(request: AgentRequest) -> AgentResult:
    return _service.review(request.request)
