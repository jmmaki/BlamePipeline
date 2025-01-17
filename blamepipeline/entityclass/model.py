#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: Shuailong
# @Email: liangshuailong@gmail.com
# @Date:   2018-05-09 11:12:33
# @Last Modified by:  Shuailong
# @Last Modified time: 2018-05-30 20:52:17

'''
EntityClassifier Class Wrapper
'''


import logging
import copy

import torch
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable

from blamepipeline.entityclass.config import override_model_args
from blamepipeline.entityclass.extractor import LSTMContextClassifier


logger = logging.getLogger(__name__)


class EntityClassifier(object):
    """High level model that handles intializing the underlying network
    architecture, saving, updating examples, and predicting examples.
    """

    # --------------------------------------------------------------------------
    # Initialization
    # --------------------------------------------------------------------------

    def __init__(self, args, word_dict, label_dict, state_dict=None):
        # Book-keeping.
        self.args = args
        self.word_dict = word_dict
        self.label_dict = label_dict
        self.args.vocab_size = len(word_dict)
        self.args.label_size = len(label_dict)
        self.updates = 0
        self.device = None
        self.parallel = False

        # Building network.
        if args.model_type == 'context':
            self.network = LSTMContextClassifier(args)
        else:
            raise RuntimeError(f'Unsupported model: {args.model_type}')

        if state_dict:
            self.network.load_state_dict(state_dict)
        # self.loss_weights = torch.tensor([])

    def load_embeddings(self, words, embedding_file):
        """Load pretrained embeddings for a given list of words, if they exist.

        Args:
            words: iterable of tokens. Only those that are indexed in the
              dictionary are kept.
            embedding_file: path to text file of embeddings, space separated.
        """
        words = {w for w in words if w in self.word_dict}
        logger.info(f'Loading pre-trained embeddings for {len(words)} words from {embedding_file}')
        embedding = self.network.embedding.weight.data

        # When normalized, some words are duplicated. (Average the embeddings).
        vec_counts = {}
        with open(embedding_file, encoding='utf-8') as f:
            for line in f:
                parsed = line.rstrip().split(' ')
                assert(len(parsed) == embedding.size(1) + 1)
                w = self.word_dict.normalize(parsed[0])
                if w in words:
                    vec = torch.Tensor([float(i) for i in parsed[1:]])
                    if w not in vec_counts:
                        vec_counts[w] = 1
                        embedding[self.word_dict[w]].copy_(vec)
                    else:
                        logging.warning(f'WARN: Duplicate embedding found for {w.encode("utf-8")}')
                        vec_counts[w] = vec_counts[w] + 1
                        embedding[self.word_dict[w]].add_(vec)

        for w, c in vec_counts.items():
            embedding[self.word_dict[w]].div_(c)

        logger.info('Loaded %d embeddings (%.2f%%)' %
                    (len(vec_counts), 100 * len(vec_counts) / len(words)))

    def init_optimizer(self, state_dict=None):
        """Initialize an optimizer for the free parameters of the network.

        Args:
            state_dict: network parameters
        """
        if self.args.fix_embeddings and self.args.pretrain_file != 'elmo':
            for p in self.network.embedding.parameters():
                p.requires_grad = False
        parameters = [p for p in self.network.parameters() if p.requires_grad]
        if self.args.optimizer == 'sgd':
            self.optimizer = optim.SGD(parameters, self.args.learning_rate,
                                       momentum=self.args.momentum,
                                       weight_decay=self.args.weight_decay)
        elif self.args.optimizer == 'adamax':
            self.optimizer = optim.Adamax(parameters,
                                          weight_decay=self.args.weight_decay,
                                          lr=self.learning_rate)
        elif self.args.optimizer == 'adam':
            self.optimizer = optim.Adam(parameters,
                                        weight_decay=self.args.weight_decay,
                                        lr=self.args.learning_rate)
        elif self.args.optimizer == 'adadelta':
            self.optimizer = optim.Adadelta(parameters,
                                            weight_decay=self.args.weight_decay,
                                            lr=self.args.learning_rate)
        else:
            raise RuntimeError(f'Unsupported optimizer: {self.args.optimizer}')

    # --------------------------------------------------------------------------
    # Learning
    # --------------------------------------------------------------------------

    def update(self, ex):
        """Forward a batch of examples; step the optimizer to update weights."""
        if not self.optimizer:
            raise RuntimeError('No optimizer set.')

        # Train mode
        self.network.train()

        # Transfer to GPU
        # inputs = [e.to(device=self.device) if not isinstance(e, (list, dict)) else e for e in ex[:-1]]
        # label = ex[-1].to(device=self.device)
        # inputs = [Variable(e.cuda()) if isinstance(e, torch.Tensor) else e for e in ex[:-1]]
        inputs = []
        for e in ex[:-1]:
            if isinstance(e, (torch.LongTensor, torch.ByteTensor, torch.cuda.LongTensor, torch.cuda.ByteTensor)):
                inputs.append(Variable(e).cuda())
            elif isinstance(e, Variable):
                inputs.append(e.cuda())
            else:
                inputs.append(e)
        label = Variable(ex[-1]).cuda()
        # Run forward
        score = self.network(*inputs)

        # Compute loss and accuracies
        loss = F.cross_entropy(score, label)

        # Clear gradients and run backward
        self.optimizer.zero_grad()
        loss.backward()

        # Clip gradients
        torch.nn.utils.clip_grad_norm(self.network.linear.parameters(),
                                      self.args.grad_clipping)

        # Update parameters
        self.optimizer.step()
        self.updates += 1

        return loss.data[0], ex[0].size(0)

    # --------------------------------------------------------------------------
    # Prediction
    # --------------------------------------------------------------------------

    def predict(self, ex):
        """
        If async_pool is given, these will be AsyncResult handles.
        """
        # Eval mode
        self.network.eval()

        # Transfer to GPU
        # inputs = [e.to(self.device) if not isinstance(e, (list, dict)) else e for e in ex]
        # inputs = [Variable(e, volatile=True).cuda() if isinstance(e, torch.Tensor) else e for e in ex]
        inputs = []
        for e in ex:
            if isinstance(e, (torch.LongTensor, torch.ByteTensor, torch.cuda.LongTensor, torch.cuda.ByteTensor)):
                inputs.append(Variable(e, volatile=True).cuda())
            elif isinstance(e, Variable):
                e.volatile = True
                inputs.append(e.cuda())
            else:
                inputs.append(e)

        # with torch.no_grad():
        #     # Run forward
        #     score = self.network(*inputs)
        score = self.network(*inputs)

        # Decode predictions
        return score.cpu().max(1)[1]

    # --------------------------------------------------------------------------
    # Saving and loading
    # --------------------------------------------------------------------------

    def save(self, filename):
        state_dict = copy.copy(self.network.state_dict())
        if 'fixed_embedding' in state_dict:
            state_dict.pop('fixed_embedding')
        params = {
            'state_dict': state_dict,
            'word_dict': self.word_dict,
            'label_dict': self.label_dict,
            'args': self.args,
        }
        try:
            torch.save(params, filename)
        except BaseException:
            logger.warning('WARN: Saving failed... continuing anyway.')

    @staticmethod
    def load(filename, new_args=None):
        logger.info(f'Loading model {filename}')
        saved_params = torch.load(
            filename, map_location=lambda storage, loc: storage
        )
        word_dict = saved_params['word_dict']
        label_dict = saved_params['label_dict']
        state_dict = saved_params['state_dict']
        args = saved_params['args']
        if new_args:
            args = override_model_args(args, new_args)
        return EntityClassifier(args, word_dict, label_dict, state_dict)

    # --------------------------------------------------------------------------
    # Runtime
    # --------------------------------------------------------------------------

    def cuda(self):
        # self.device = device
        self.network = self.network.cuda()
        # self.loss_weights = self.loss_weights.to(device)

    def parallelize(self):
        """Use data parallel to copy the model across several gpus.
        This will take all gpus visible with CUDA_VISIBLE_DEVICES.
        """
        self.parallel = True
        self.network = torch.nn.DataParallel(self.network)
