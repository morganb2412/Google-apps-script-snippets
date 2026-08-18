import hashlib
import json

from app.appsscript.models import (
    AppsScriptContent,
    AppsScriptFile,
    AppsScriptFileType,
    ProjectFile,
    ProjectFileSource,
    ProjectSnapshot,
)

EXTENSIONS = {
    AppsScriptFileType.SERVER_JS: ".gs",
    AppsScriptFileType.HTML: ".html",
    AppsScriptFileType.JSON: ".json",
}


def normalize_file(file: AppsScriptFile) -> ProjectFile:
    extension = EXTENSIONS[file.type]
    path = file.name if file.name.endswith(extension) else f"{file.name}{extension}"
    content = file.source.replace("\r\n", "\n").replace("\r", "\n")
    return ProjectFile(
        path=path,
        name=file.name,
        extension=extension,
        content=content,
        sha256=_sha256(content),
        source=ProjectFileSource.APPS_SCRIPT,
        metadata={"apps_script_type": file.type.value},
    )


def create_snapshot(content: AppsScriptContent) -> ProjectSnapshot:
    files = sorted((normalize_file(file) for file in content.files), key=lambda item: item.path)
    digest_input = "\n".join(f"{file.path}:{file.sha256}" for file in files)
    return ProjectSnapshot(
        script_id=content.script_id,
        project_hash=_sha256(digest_input),
        files=files,
    )


def manifest_scopes(files: list[AppsScriptFile]) -> set[str]:
    manifest = next(
        (
            file
            for file in files
            if file.type is AppsScriptFileType.JSON and file.name == "appsscript"
        ),
        None,
    )
    if manifest is None:
        return set()
    try:
        payload = json.loads(manifest.source)
    except json.JSONDecodeError as error:
        raise ValueError("appsscript.json is not valid JSON.") from error
    scopes = payload.get("oauthScopes", [])
    if not isinstance(scopes, list) or not all(isinstance(scope, str) for scope in scopes):
        raise ValueError("appsscript.json oauthScopes must be a list of strings.")
    return set(scopes)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
