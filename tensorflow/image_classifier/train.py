from matplotlib import pyplot as plt
import os
import datetime
import tensorflow as tf
from tensorflow.keras import datasets, layers, models

dir = (os.path.abspath(os.path.dirname(__file__)))

BATCH_SIZE = 100


def load_image(img_path, size=(32, 32)):
    label = tf.constant(1, tf.int8) if tf.strings.regex_full_match(img_path, ".*automobile.*") \
        else tf.constant(0, tf.int8)
    img = tf.io.read_file(img_path)
    img = tf.image.decode_jpeg(img)  # 注意此处为jpeg格式
    img = tf.image.resize(img, size)/255.0
    return(img, label)


# 使用并行化预处理num_parallel_calls 和预存数据prefetch来提升性能
ds_train = tf.data.Dataset.list_files(dir+"/cifar2/train/*/*.jpg") \
    .map(load_image, num_parallel_calls=tf.data.experimental.AUTOTUNE) \
    .shuffle(buffer_size=1000).batch(BATCH_SIZE) \
    .prefetch(tf.data.experimental.AUTOTUNE)

ds_test = tf.data.Dataset.list_files(dir+"/cifar2/test/*/*.jpg") \
    .map(load_image, num_parallel_calls=tf.data.experimental.AUTOTUNE) \
    .batch(BATCH_SIZE) \
    .prefetch(tf.data.experimental.AUTOTUNE)
# 查看部分样本

plt.figure(figsize=(8, 8))
for i, (img, label) in enumerate(ds_train.unbatch().take(9)):
    ax = plt.subplot(3, 3, i+1)
    ax.imshow(img.numpy())
    ax.set_title("label = %d" % label)
    ax.set_xticks([])
    ax.set_yticks([])
plt.show()


def createModel():
    inputs = layers.Input(shape=(32, 32, 3))
    x = layers.Conv2D(32, kernel_size=(3, 3))(inputs)
    x = layers.MaxPool2D()(x)
    x = layers.Conv2D(64, kernel_size=(5, 5))(x)
    x = layers.MaxPool2D()(x)
    x = layers.Dropout(rate=0.1)(x)
    x = layers.Flatten()(x)
    x = layers.Dense(32, activation='relu')(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)

    return models.Model(inputs=inputs, outputs=outputs)


model = createModel()
model.summary()

stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
logdir = dir + "/log_"+stamp


tensorboard_callback = tf.keras.callbacks.TensorBoard(logdir, histogram_freq=1)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss=tf.keras.losses.binary_crossentropy,
    metrics=["accuracy"]
)

history = model.fit(ds_train, epochs=10, validation_data=ds_test,
                    callbacks=[tensorboard_callback], workers=4)

val_loss, val_accuracy = model.evaluate(ds_test, workers=4)
print(val_loss, val_accuracy)

result = model.predict(ds_test)
print(result)

model.save(dir+'/tf_model', save_format="tf")
