#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: Shuailong
# @Email: liangshuailong@gmail.com
# @Date:   2018-05-09 11:12:33
# @Last Modified by:  Shuailong
# @Last Modified time: 2018-05-10 16:03:23

#fixed relative import statement
from blamepipeline import DATA_DIR

DEFAULTS = {

}


def set_default(key, value):
    global DEFAULTS
    DEFAULTS[key] = value

#fixed relative import statement
from blamepipeline.simplebaseline.model import BlameExtractor as BaselineModel
