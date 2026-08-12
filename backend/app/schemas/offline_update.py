from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel


class OfflineUpdateStepOut(BaseModel):
    title: str
    description: str
    status: str
    last_updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OfflineUpdateStepListOut(BaseModel):
    steps: List[OfflineUpdateStepOut]


class OfflineUpdateHistoryOut(BaseModel):
    id: Optional[int] = None
    package_id: Optional[str] = None
    version: Optional[str] = None
    package_name: Optional[str] = None
    installed_by: Optional[str] = None
    install_time: Optional[datetime] = None
    checksum_status: Optional[str] = None
    signature_status: Optional[str] = None
    status: Optional[str] = None
    rollback_version: Optional[str] = None
    remarks: Optional[str] = None

    model_config = {"from_attributes": True}


class OfflineUpdateHistoryListOut(BaseModel):
    history: List[OfflineUpdateHistoryOut]


class OfflineUpdateImportResponse(BaseModel):
    package_name: str
    package_id: str
    version: str
    created_date: str
    status: str
    session_id: str


class OfflineUpdateVerifyResponse(BaseModel):
    manifest_pass: bool
    checksum_pass: bool
    signature_pass: bool
    malware_pass: bool
    overall_status: str
    package_name: Optional[str] = None
    package_id: Optional[str] = None
    version: Optional[str] = None
    session_id: Optional[str] = None


class OfflineUpdateInstallResponse(BaseModel):
    step: str
    status: str
    message: str
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    progress: List[str]
    request_id: Optional[UUID] = None


class OfflineUpdateBackupsOut(BaseModel):
    versions: List[str]


class OfflineUpdateActionResponse(BaseModel):
    step: str
    status: str
    message: str
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    request_id: Optional[UUID] = None
