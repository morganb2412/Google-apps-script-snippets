import hashlib

from app.appsscript.models import ProjectFile, ProjectFileSource, ProjectSnapshot
from app.github.models import GitHubFile


def create_github_snapshot(script_id: str, repository_files: list[GitHubFile]) -> ProjectSnapshot:
    files = sorted(
        (
            ProjectFile(
                path=file.path,
                name=file.name,
                extension=_extension(file.path),
                content=file.content.replace("\r\n", "\n").replace("\r", "\n"),
                sha256=_sha256(file.content.replace("\r\n", "\n").replace("\r", "\n")),
                source=ProjectFileSource.GITHUB,
                metadata={"github_blob_sha": file.sha},
            )
            for file in repository_files
        ),
        key=lambda item: item.path,
    )
    digest_input = "\n".join(f"{file.path}:{file.sha256}" for file in files)
    return ProjectSnapshot(script_id=script_id, project_hash=_sha256(digest_input), files=files)


def _extension(path: str) -> str:
    filename = path.rsplit("/", 1)[-1]
    return f".{filename.rsplit('.', 1)[-1]}" if "." in filename else ""


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
