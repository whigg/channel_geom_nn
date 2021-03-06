import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf

import plot_utils

tf.reset_default_graph()

# read the data
# df = pd.read_csv('data/mcelroy_dataclean.csv') # read data set using pandas
# df = pd.read_csv('data/wilkerson_dataclean.csv') # read data set using pandas
df = pd.read_csv('data/ShieldsJHRData.csv') # read data set using pandas
df = df.dropna(inplace = False)  # Remove all nan entries.

print('Data summary:\n')
print(df.describe(), '\n\n') # Overview of dataset

# subset for train and test and rescale all values
df_train, df_test = train_test_split(df, test_size=0.30)

# we want to predict the H, B, and S given Qbf, D50
# this only works because HBS are highly correlated.
# y is output and x is input features

# do some normalization
scaler = MinMaxScaler() # For normalizing dataset

# min max normalization
# X_train = scaler.fit_transform(df_train.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values)
# y_train = scaler.fit_transform(df_train[['Bbf.m', 'Hbf.m', 'S']].values)
# X_test = scaler.fit_transform(df_test.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values)
# y_test = scaler.fit_transform(df_test[['Bbf.m', 'Hbf.m', 'S']].values)

# min max log(x) normalization
# X_train = scaler.fit_transform(np.log10(df_train.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values))
# y_train = scaler.fit_transform(np.log10(df_train[['Bbf.m', 'Hbf.m', 'S']].values))
# X_test = scaler.fit_transform(np.log10(df_test.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values))
# y_test = scaler.fit_transform(np.log10(df_test[['Bbf.m', 'Hbf.m', 'S']].values))
# logged = True
# normed = True

# log(x) normalization
X_train = (np.log10(df_train.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values))
y_train = (np.log10(df_train[['Bbf.m', 'Hbf.m', 'S']].values))
X_test = (np.log10(df_test.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values))
y_test = (np.log10(df_test[['Bbf.m', 'Hbf.m', 'S']].values))
logged = True
normed = False

# no normalization (be sure to turn off below for plotting)
# X_train = (df_train.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values)
# y_train = (df_train[['Bbf.m', 'Hbf.m', 'S']].values)
# X_test = (df_test.drop(['Bbf.m', 'Hbf.m', 'S'], axis=1).values)
# y_test = (df_test[['Bbf.m', 'Hbf.m', 'S']].values)
# logged = False
# normed = False

# set up data for mini-batching during training
batch_size = 1
buffer_size = 15
ds_train = tf.data.Dataset.from_tensor_slices((X_train, y_train)).repeat().batch(batch_size).shuffle(buffer_size)
it_train = ds_train.make_one_shot_iterator()
xs, ys = it_train.get_next()


def denormalize(df, norm_data):
    """
    Above written function for denormalization of data after normalizing
    this function will give original scale of values.
    """

    if logged:
        df = np.log10(df[['Bbf.m', 'Hbf.m', 'S']].values)
    else:
        df = df[['Bbf.m', 'Hbf.m', 'S']].values

    if normed:
        scl = MinMaxScaler()
        a = scl.fit_transform(df)
        new = scl.inverse_transform(norm_data)
    else:
        new = norm_data
    
    if logged:
        expt = np.power(10, new)
        return expt
    else:
        return new


def nn_model(X_data, input_dim):
    """
    nn_model constructs the neural network model. 
    It can be a 1 layer or 2 layer model, with n_nodes.
    Weights and biases are abberviated as W_1, W_2 and b_1, b_2 
    """

    n_nodes = 1

    # layer 1 multiplying and adding bias then activation function
    W_1 = tf.Variable(tf.random_uniform([input_dim, n_nodes], dtype='float64'))
    b_1 = tf.Variable(tf.zeros([n_nodes], dtype = 'float64'))
    layer_1 = tf.add(tf.matmul(X_data, W_1), b_1)
    layer_1 = tf.nn.relu(layer_1)

    # layer 2 multiplying and adding bias then activation function    
    # W_2 = tf.Variable(tf.random_uniform([n_nodes, n_nodes], dtype='float64'))
    # b_2 = tf.Variable(tf.zeros([n_nodes], dtype = 'float64'))
    # layer_2 = tf.add(tf.matmul(layer_1, W_2), b_2)
    # layer_2 = tf.nn.relu(layer_2)

    # output layer multiplying and adding bias then activation function
    W_O = tf.Variable(tf.random_uniform([n_nodes, 3], dtype = 'float64')) # 3 because there are two outputs
    b_O = tf.Variable(tf.zeros([3], dtype = 'float64'))
    output = tf.add(tf.matmul(layer_1, W_O), b_O)
    # output = tf.add(tf.matmul(layer_2, W_O), b_O)

    return output, W_O


# the model
output, W_O = nn_model(xs, X_train.shape[1])

# mean squared error cost function
# loss = tf.reduce_sum(tf.square(output - ys))
# loss = tf.reduce_mean(tf.square(output - ys))
loss = tf.losses.mean_squared_error(output, ys)

# Gradinent Descent optimiztion just discussed above for updating weights and biases
learning_rate = 0.01
train = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss)
# train = tf.train.AdamOptimizer(learning_rate).minimize(loss)

# some other initializations
_loss_summary = tf.summary.scalar(name='loss summary', tensor=loss)
# correct_pred = tf.argmax(output, 1)
# accuracy = tf.losses.mean_squared_error(tf.cast(correct_pred, tf.float32), ys)
# saver = tf.train.Saver()

c_train = []
c_test = []

save_training = False
with tf.Session() as sess:
    # Initiate session and initialize all vaiables
    sess.run(tf.global_variables_initializer())

    writer = tf.summary.FileWriter("log/", sess.graph)

    it = 0
    n_epoch = 10
    n_batch_per_epoch = int( np.floor(X_train.shape[0] / batch_size) )
    for i in range(n_epoch):
        ds_train.shuffle(buffer_size)
        for j in range(n_batch_per_epoch):
            # Run loss and train with each batch
            sess.run([loss, train])

            c_train.append(sess.run(loss, feed_dict = {xs:X_train, ys:y_train}))
            c_test.append(sess.run(loss, feed_dict = {xs:X_test, ys:y_test}))

            loss_summary = sess.run(_loss_summary)
            writer.add_summary(loss_summary, it)

            if save_training:
                

                intrain_pred_test = sess.run(output, feed_dict={xs:X_test})
                intrain_pred_train = sess.run(output, feed_dict={xs:X_train})

                intrain_y_test = denormalize(df_test, y_test)
                intrain_pred_test = denormalize(df_test, intrain_pred_test)
                intrain_y_train = denormalize(df_train, y_train)
                intrain_pred_train = denormalize(df_train, intrain_pred_train)
                figN = plot_utils.compare_plot(df, df_train, df_test, intrain_pred_train, intrain_pred_test)
                figN.savefig('figures/training/{:04d}.png'.format(it))
                plt.close(figN)
                print('Epoch:', i, ', train loss:', c_train[i*n_batch_per_epoch], ', test loss:', c_test[i*n_batch_per_epoch])

            it += 1
        
        print('Epoch:', i, ', train loss:', c_train[i*n_batch_per_epoch], ', test loss:', c_test[i*n_batch_per_epoch])

    # finished training
    print('\nTraining complete.')
    print('Total iterations: ', it)
    print('test loss :', sess.run(loss, feed_dict={xs:X_test, ys:y_test}), '\n')
    writer.close()

    # save the model
    # save_path = saver.save(sess, "log/channel_geom_nn_QDtoHBS.ckpt")

    # predict output of test data after training
    pred_test = sess.run(output, feed_dict={xs:X_test})
    pred_train = sess.run(output, feed_dict={xs:X_train})

    # predict for some range
    qlist = np.array([2000, 3000])
    dlist = np.linspace(1, 20, num=19) # np.array([1.0, 5.0, 10, 100])
    bhs = np.empty((qlist.shape[0]*dlist.shape[0], 3))
    dep = 0
    for q in iter(qlist):
        for d in iter(dlist):
            invect = np.log10( np.array([q, d]).reshape(-1, 2) )
            pred_rng = sess.run(output, feed_dict={xs:invect})
            pred_dn = denormalize(df_test, pred_rng)
            bhs[dep, :] = pred_dn
            dep += 1
    bhs = bhs.reshape((dlist.shape[0], 3, -1))   

# denormalize data
y_test = denormalize(df_test, y_test)
pred_test = denormalize(df_test, pred_test)
y_train = denormalize(df_train, y_train)
pred_train = denormalize(df_train, pred_train)


# plots
fig1, axes1 = plt.subplots(nrows=1, ncols=2, figsize=(6,4))
axes1[0].hist([df_train['Qbf.m3s'], df_test['Qbf.m3s']], histtype = 'bar', density = True)
axes1[0].set_xlabel('Qbf (m3/s)')
axes1[1].hist([df_train['D50.mm'], df_test['D50.mm']], histtype = 'bar', density = True)
axes1[1].set_xlabel('D50 (mm)')
plt.legend(['train', 'test'], loc = 'best')
fig1.savefig('figures/split.png')

fig2 = plot_utils.compare_plot(df, df_train, df_test, pred_train, pred_test)
fig2.savefig('figures/compare.png')

fig3, ax3 = plt.subplots(figsize=(6,4))
ax3.plot(np.arange(len(c_train)) / n_batch_per_epoch, np.array(c_train))
ax3.plot(np.arange(len(c_test)) / n_batch_per_epoch, np.array(c_test))
ax3.set_xlabel('epoch')
ax3.set_ylabel('loss')
plt.legend(['train', 'test'], loc = 'best')
fig3.savefig('figures/train.png')

fig4, ax4 = plt.subplots(figsize=(8,6))
pd.plotting.scatter_matrix(np.log10(df), ax=ax4)
fig4.savefig('figures/scatter.png')

fig5, ax5 = plt.subplots()
ax5.matshow(np.log10(df).corr())
fig5.savefig('figures/corr_mat.png')

fig6, ax6 = plt.subplots(nrows=3, ncols=1, figsize=(6,10))
ax6[0].scatter(df['D50.mm'], df['Hbf.m'])
for p in np.arange(bhs.shape[2]):
    ax6[0].plot(dlist, bhs[:, 1, p])
    ax6[0].set_ylabel('depth (m)')
ax6[1].scatter(df['D50.mm'], df['Bbf.m'])
for p in np.arange(bhs.shape[2]):
    ax6[1].plot(dlist, bhs[:, 0, p])
    ax6[1].set_ylabel('width (m)')
ax6[2].scatter(df['D50.mm'], df['S'])
for p in np.arange(bhs.shape[2]):
    ax6[2].plot(dlist, bhs[:, 2, p])
    ax6[2].set_ylabel('slope (1)')
ax6[2].set_yscale('log')
# ax6[0].set_xscale('log')
ax6[0].legend(qlist)
# plt.show()

fig6.savefig('figures/input_test.png')