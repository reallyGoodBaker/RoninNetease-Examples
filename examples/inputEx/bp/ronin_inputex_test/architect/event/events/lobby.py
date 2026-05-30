# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class lobbyGoodBuySucServerEvent(ChainedEvent):
    """服务端 - 玩家登录联机大厅服务器或购买商品时触发"""
    eid = None     # type: str
    buyItem = None # type: bool