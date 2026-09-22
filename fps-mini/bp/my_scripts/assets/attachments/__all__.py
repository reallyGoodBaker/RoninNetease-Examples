# -*- coding: utf-8 -*-
# 这个文件的作用在于提前导入这些模块让模块搜索功能能正常运行

from .appearance.__all__ import *

from . import (
    bayonet,
    template,
    fov1_5x,
    fov1x,
    fov2x,
    telescope3x,
    telescope10x,
    mp18_drum,
    mp18_magazine,
    smle_mk3_quickshoot,
    mosin_obrez,
)