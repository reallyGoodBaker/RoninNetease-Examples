# -*- coding: utf-8 -*-
from .interface import ChainedEvent


class PhysxTouchClientEvent(ChainedEvent):
    """客户端 - 给自定义刚体添加的碰撞体，与其他碰撞体或原版实体发生碰撞/结束碰撞时触发。需要在碰撞体创建时使用PxEventMask.Client才会触发"""
    touch = None  # type: list[dict]
    lost = None   # type: list[dict]


class PhysxTouchServerEvent(ChainedEvent):
    """服务端 - 给自定义刚体添加的碰撞体，与其他碰撞体或原版实体发生碰撞/结束碰撞时触发。需要在碰撞体创建时使用PxEventMask.Server才会触发"""
    touch = None  # type: list[dict]
    lost = None   # type: list[dict]


class PhysxTriggerClientEvent(ChainedEvent):
    """客户端 - 给自定义刚体添加的触发器，与其他碰撞体或原版实体进入/离开触发器时触发。需要在触发器创建时使用PxEventMask.Client才会触发"""
    found = None  # type: list[dict]
    lost = None   # type: list[dict]


class PhysxTriggerServerEvent(ChainedEvent):
    """服务端 - 给自定义刚体添加的触发器，与其他碰撞体或原版实体发生进入触发器/离开触发器时触发。需要在触发器创建时使用PxEventMask.Server才会触发"""
    found = None  # type: list[dict]
    lost = None   # type: list[dict]