#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Model architecture/optimization options for Blame Extractor."""

import argparse
import logging

logger = logging.getLogger(__name__)

# Index of arguments concerning the core model architecture
MODEL_ARCHITECTURE = {
    'model_type', 'embedding_dim', 'hidden_size', 'layers',
    'rnn_type', 'concat_rnn_layers', 'kernel_sizes', 'unk_entity',
    'feature_size', 'pretrain_file', 'elmo_options_file', 'elmo_weights_file',
    'skip_rnn', 'bidirectional', 'pooling', 'entity_embs', 'entity_embedding_dim'
}

# Index of arguments concerning the model optimizer/training
MODEL_OPTIMIZER = {
    'fix_embeddings', 'optimizer', 'learning_rate', 'momentum', 'weight_decay',
    'rnn_padding', 'dropout_rnn', 'dropout_cnn', 'dropout_rnn_output', 'dropout_emb',
    'grad_clipping', 'dropout_feature', 'dropout_final', 'pos_weight', 'xavier_init'
}


def str2bool(v):
    return v.lower() in ('yes', 'true', 't', '1', 'y')


def add_model_args(parser):
    parser.register('type', 'bool', str2bool)

    # Model architecture
    model = parser.add_argument_group('Blame Extractor BiLSTM Model Architecture')
    model.add_argument('--model-type', type=str, default='context',
                       choices=['context', 'entity'],
                       help='Model architecture type')
    model.add_argument('--unk-entity', type='bool', default=True,
                       help='Mask entity work by PAD symbol')
    model.add_argument('--embedding-dim', type=int, default=100,
                       help='Embedding size if embedding_file is not given')
    model.add_argument('--entity-embedding-dim', type=int, default=50,
                       help='Entity embedding size')
    model.add_argument('--hidden-size', type=int, default=100,
                       help='Hidden size of RNN/CNN units')
    model.add_argument('--feature-size', type=int, default=20,
                       help='final feature layer')
    model.add_argument('--layers', type=int, default=1,
                       help='Number of encoding layers for sentence')
    model.add_argument('--rnn-type', type=str, default='lstm',
                       help='RNN type: LSTM, GRU, or RNN')
    model.add_argument('--bidirectional', type='bool', default=True,
                       help='Whether to use BiLSTM')
    model.add_argument('--pooling', type=str, default='mean',
                       choices=['rand', 'max', 'mean', 'attn'],
                       help='pooling entity representations')
    model.add_argument('--entity-embs', type='bool', default=False,
                       help='include entity embeddings')
    model.add_argument('--skip-rnn', type='bool', default=False,
                       help='Skip RNN layer. Use embeddings directly.')
    model.add_argument('--kernel-sizes', type=int, nargs='+', default=[3, 4, 5],
                       help='CNN kernel sizes')

    # Model specific details
    detail = parser.add_argument_group('Blame Extractor BiLSTM Model Details')
    detail.add_argument('--concat-rnn-layers', type='bool', default=False,
                        help='Combine hidden states from each encoding layer')

    # Optimization details
    optim = parser.add_argument_group('Blame Extractor Optimization')
    optim.add_argument('--dropout-emb', type=float, default=0.5,
                       help='Dropout rate for word embeddings')
    optim.add_argument('--dropout-rnn', type=float, default=0.0,
                       help='Dropout rate for RNN states')
    optim.add_argument('--dropout-cnn', type=float, default=0.5,
                       help='Dropout rate for CNN output')
    optim.add_argument('--dropout-rnn-output', type='bool', default=True,
                       help='Whether to dropout the RNN output')
    optim.add_argument('--dropout-feature', type=float, default=0.5,
                       help='Feature layer dropout')
    optim.add_argument('--dropout_final', type=float, default=0.5,
                       help='Final layer dropout')
    optim.add_argument('--optimizer', type=str, default='adam',
                       help='Optimizer: sgd or adam')
    optim.add_argument('--xavier-init', type='bool', default=False,
                       help='Xavier initialization')
    optim.add_argument('--learning-rate', type=float, default=1e-3,
                       help='Initial learning rate')
    optim.add_argument('--grad-clipping', type=float, default=3,
                       help='Gradient clipping')
    optim.add_argument('--weight-decay', type=float, default=1e-8,
                       help='Weight decay factor')
    optim.add_argument('--momentum', type=float, default=0,
                       help='Momentum factor')
    optim.add_argument('--fix-embeddings', type='bool', default=False,
                       help='Keep word embeddings fixed (use pretrained)')
    optim.add_argument('--rnn-padding', type='bool', default=False,
                       help='Explicitly account for padding in RNN encoding')
    optim.add_argument('--weighted-sampling', type='bool', default=False,
                       help='Weighted sampling during training')
    optim.add_argument('--pos-weight', type=float, default=0.5,
                       help='Weighted cross entropy loss')


def get_model_args(args):
    """Filter args for model ones.

    From a args Namespace, return a new Namespace with *only* the args specific
    to the model architecture or optimization. (i.e. the ones defined here.)
    """
    global MODEL_ARCHITECTURE, MODEL_OPTIMIZER
    required_args = MODEL_ARCHITECTURE | MODEL_OPTIMIZER
    arg_values = {k: v for k, v in vars(args).items() if k in required_args}
    return argparse.Namespace(**arg_values)


def override_model_args(old_args, new_args):
    """Set args to new parameters.

    Decide which model args to keep and which to override when resolving a set
    of saved args and new args.

    We keep the new optimation, but leave the model architecture alone.
    """
    global MODEL_OPTIMIZER
    old_args, new_args = vars(old_args), vars(new_args)
    for k in old_args.keys():
        if k in new_args and old_args[k] != new_args[k]:
            if k in MODEL_OPTIMIZER:
                logger.info('Overriding saved %s: %s --> %s' %
                            (k, old_args[k], new_args[k]))
                old_args[k] = new_args[k]
            else:
                logger.info('Keeping saved %s: %s' % (k, old_args[k]))
    return argparse.Namespace(**old_args)
