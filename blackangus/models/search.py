import dataclasses


@dataclasses.dataclass
class GoogleImagesModel:
    image_link: str
    title: str
    destination_link: str


@dataclasses.dataclass
class YoutubeModel:
    thumbnail_link: str
    duration: str
    title: str
    description: str
    uploader: str
    link: str
