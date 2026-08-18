from app.models.project import ProjectContextRequest, ProjectContextResponse


class ProjectContextService:
    def validate(self, context: ProjectContextRequest) -> ProjectContextResponse:
        return ProjectContextResponse(
            script_id=context.script_id,
            name=context.name.strip() if context.name and context.name.strip() else None,
            editor_url=str(context.editor_url),
            detected_at=context.detected_at,
        )


def get_project_context_service() -> ProjectContextService:
    return ProjectContextService()
