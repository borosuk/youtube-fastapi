from pydantic import BaseModel

class ChannelPageInfo(BaseModel):
    totalResults: int
    resultsPerPage: int

class ChannelLocalized(BaseModel):
    title: str
    description: str

class ChannelRelatedPlaylists(BaseModel):
    likes: str
    uploads: str

class ChannelContentDetails(BaseModel):
    relatedPlaylists: ChannelRelatedPlaylists

class ChannelSnippet(BaseModel):
    title: str
    description: str
    customUrl: str
    publishedAt: str
    localized: ChannelLocalized
    country: str

class ChannelItem(BaseModel):
    kind: str
    etag: str
    id: str
    snippet: ChannelSnippet
    contentDetails: ChannelContentDetails

class ChannelRoot(BaseModel):
    kind: str
    etag: str
    pageInfo: ChannelPageInfo
    items: list[ChannelItem]
