from pydantic import BaseModel


class VideoId(BaseModel):
    kind: str
    videoId: str

class VideoSnippet(BaseModel):
    publishedAt: str
    channelId: str
    title: str
    description: str
    channelTitle: str
    liveBroadcastContent: str
    publishTime: str

class VideoPageInfo(BaseModel):
    totalResults: int
    resultsPerPage: int

class VideoItem(BaseModel):
    kind: str
    etag: str
    id: VideoId
    snippet: VideoSnippet

class VideoRoot(BaseModel):
    kind: str
    etag: str
    nextPageToken: str
    pageInfo: VideoPageInfo
    items: list[VideoItem]