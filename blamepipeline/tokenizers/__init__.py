#!/usr/bin/env python3
# Copyright 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import os
import blamepipeline
import spacy
from blamepipeline import tokenizers

try:
    from spacy.spacy_tokenizer import SpacyTokenizer
except ImportError:
    pass

DEFAULTS = {

}


def set_default(key, value):
    global DEFAULTS
    DEFAULTS[key] = value


from blamepipeline.tokenizers.corenlp_tokenizer import CoreNLPTokenizer

# Spacy is optional



def get_class(name):
    if name == 'spacy':
        return SpacyTokenizer
    if name == 'corenlp':
        return CoreNLPTokenizer

    raise RuntimeError('Invalid tokenizer: %s' % name)

