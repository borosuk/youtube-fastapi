from pydantic import BaseModel


class PlaylistContentDetails(BaseModel):
    itemCount: int

class PlaylistSnippet(BaseModel):
    publishedAt: str
    channelId: str
    title: str
    description: str
    channelTitle: str
	  
class PlaylistItem(BaseModel):
    kind: str
    etag: str
    id: str
    snippet: PlaylistSnippet
    contentDetails: PlaylistContentDetails	  

class PlaylistPageInfo(BaseModel):
    totalResults: int
    resultsPerPage: int

class PlaylistRoot(BaseModel):
    kind: str
    etag: str
    nextPageToken: str
    pageInfo: PlaylistPageInfo
    items: list[PlaylistItem]