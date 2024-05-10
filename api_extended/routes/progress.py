import re

from litestar import Controller, Request, Router, delete, get, post
from litestar.datastructures import State
from litestar.exceptions import ValidationException
from pydantic import BaseModel
from tortoise import connections

from api_extended.database import VideosTable

YOUTUBE_ID_REGEX_COMPLIED = re.compile(r"[a-zA-Z0-9_-]{11}")


class SaveProgressModel(BaseModel):
    time: float


class ProgressModel(SaveProgressModel):
    video_id: str


class VideoController(Controller):
    path = "/video/{video_id:str}"

    @get(
        description="You can pass video IDs comma separated up to 100 IDs to get multiple video progresses."
    )
    async def progress(
        self, request: Request[str, str, State], video_id: str
    ) -> list[ProgressModel]:
        results = await VideosTable.filter(
            video_id__in=video_id.split(","), username=request.user
        ).limit(100)

        progresses = []
        for result in results:
            progresses.append(ProgressModel(time=result.time, video_id=result.video_id))

        return progresses

    @delete()
    async def delete_progress(
        self, request: Request[str, str, State], video_id: str
    ) -> None:
        if not YOUTUBE_ID_REGEX_COMPLIED.fullmatch(video_id):
            raise ValidationException()

        await VideosTable.filter(video_id=video_id, username=request.user).delete()

    @post()
    async def save_progress(
        self, request: Request[str, str, State], data: SaveProgressModel, video_id: str
    ) -> None:

        if not YOUTUBE_ID_REGEX_COMPLIED.fullmatch(video_id):
            raise ValidationException()

        await VideosTable.update_or_create(
            video_id=video_id, username=request.user, defaults={"time": data.time}
        )


@delete("/videos", description="Deletes all watch progress for a user.")
async def delete_all_watch(request: Request[str, str, State]) -> None:
    await VideosTable.filter(username=request.user).delete()


async def crontab_check_for_deleted() -> None:
    """Background task to check if a user has deleted their Invidious account."""

    results = await connections.get("default").execute_query_dict(
        "SELECT email FROM users"
    )

    invidious_usernames: list[str] = [result["email"] for result in results]

    syncious_usernames = (
        await VideosTable.filter().distinct().values_list("username", flat=True)
    )

    to_delete = []

    for syncious_username in syncious_usernames:
        if syncious_username in invidious_usernames:
            continue

        to_delete.append(syncious_username)

    if to_delete:
        await VideosTable.filter(username__in=to_delete).delete()


router = Router(
    "/progress", route_handlers=[VideoController, delete_all_watch], tags=["progress"]
)
