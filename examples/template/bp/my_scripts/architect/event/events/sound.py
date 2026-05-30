# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class OnMusicStopClientEvent(ChainedEvent):
    """客户端 - 音乐停止时触发"""
    musicName = None # type: str


class PlayMusicClientEvent(ChainedEvent):
    """客户端 - 播放背景音乐时触发"""
    name = None   # type: str
    cancel = None # type: bool


class PlaySoundClientEvent(ChainedEvent):
    """客户端 - 播放场景音效或UI音效时触发"""
    name = None   # type: str
    pos = None    # type: tuple
    volume = None # type: float
    pitch = None  # type: float
    cancel = None # type: bool