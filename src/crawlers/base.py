from dataclasses import dataclass, field


@dataclass
class CrawlResult:
    url: str
    title: str = ""
    author: str = ""
    text: str = ""
    source_type: str = ""  # twitter, article, generic
    error: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.text) and not self.error
