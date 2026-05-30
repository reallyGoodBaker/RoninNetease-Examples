# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class AttackAnimBeginClientEvent(ChainedEvent):
    """客户端 - 攻击动作开始时触发"""
    id = None # type: str


class AttackAnimBeginServerEvent(ChainedEvent):
    """服务端 - 当攻击动作开始时触发"""
    id = None # type: str


class AttackAnimEndClientEvent(ChainedEvent):
    """客户端 - 攻击动作结束时触发"""
    id = None # type: str


class AttackAnimEndServerEvent(ChainedEvent):
    """服务端 - 当攻击动作结束时触发"""
    id = None # type: str


class JumpAnimBeginServerEvent(ChainedEvent):
    """服务端 - 当跳跃动作开始时触发"""
    id = None # type: str


class WalkAnimBeginClientEvent(ChainedEvent):
    """客户端 - 走路动作开始时触发"""
    id = None # type: str


class WalkAnimBeginServerEvent(ChainedEvent):
    """服务端 - 当走路动作开始时触发"""
    id = None # type: str


class WalkAnimEndClientEvent(ChainedEvent):
    """客户端 - 走路动作结束时触发"""
    id = None # type: str


class WalkAnimEndServerEvent(ChainedEvent):
    """服务端 - 当走路动作结束时触发"""
    id = None # type: str