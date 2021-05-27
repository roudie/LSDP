from dataclasses import dataclass, field
from typing import List


def create_list_of_lists():
    return [[] for x in range(1)]


@dataclass
class RedditPost:
    title: str = "title"
    url: str = "url"
    author: str = "author"
    subreddit: str = "subreddit"
    text: str = "text"
    text_emb: List[List[float]] = field(default_factory=create_list_of_lists)
    num_votes: int = 0
    nfsw: bool = False
    num_comm: int = 0