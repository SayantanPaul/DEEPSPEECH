import configparser, sys, os
import tensorflow as tf, numpy as np
import fnn, rnn, cnn, ce, speakerutil

def dsi(config):
	model = dict()

	model = cnn.cnn(model, config, 'cnn')
	model = rnn.rnn(model, config, 'rnn', 'cnn')
	model = fnn.fnn(model, config, 'fnn', 'rnn')
	model = ce.ce(model, config, 'ce', 'fnn')

	model['loss'] = model['ce_loss']
	model['step'] = tf.Variable(0, trainable = False, name = 'step')
	model['lrate'] = tf.train.exponential_decay(config.getfloat('global', 'lrate'), model['step'], config.getint('global', 'dstep'), config.getfloat('global', 'drate'), staircase = False, name = 'lrate')
	model['optim'] = getattr(tf.train, config.get('global', 'optim'))(model['lrate']).minimize(model['loss'], global_step = model['step'], name = 'optim')

	return model

def feed(features, labelslen, labelsind, labelsval, batch_size, time_size):
	feed_dict = {model['cnn_inputs']: [[features[i][:, t] if t < labelslen[i] else np.zeros(features[i][:, labelslen[i] - 1].shape, np.float32) for i in xrange(batch_size)] for t in xrange(time_size)]}
	feed_dict.update({model['cnn_in2length']: [features[i].shape[1] for i in xrange(batch_size)], model['ce_labels_len']: labelslen, model['ce_labels_ind']: labelsind, model['ce_labels_val']: labelsval})
	return feed_dict

if __name__ == '__main__':
	config = configparser.ConfigParser(interpolation = configparser.ExtendedInterpolation())
	config.read(sys.argv[1])
	model = dsi(config)
	speakers = speakerutil.speakermap(sys.argv[2])

	with tf.Session() as sess:
		sess.run(tf.initialize_all_variables())
		speakerutil.train(model, sess, config, sys.argv[3], feed, speakers)
		print speakerutil.test(model, sess, config, sys.argv[4], feed, speakers)
		tf.train.Saver().save(sess, os.path.join(config.get('global', 'path'), 'model'))