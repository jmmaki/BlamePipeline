#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import sys
from pathlib import PosixPath

if sys.version_info < (3, 5):
    raise RuntimeError('RLQA supports Python 3.5 or higher.')

DATA_DIR =(
    os.getenv('BLAME_DATA') or
    os.path.join(PosixPath(__file__).absolute().parents[1].as_posix(), 'data')
)

#changed the relative import statement to an absolute import to fix "no known parent package" error
from blamepipeline import claimclass
