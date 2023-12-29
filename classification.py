# -*- coding: utf-8 -*-
"""image_classification_model_deployment (2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WlHEWbASovL3YkNOvwIPmb5xl_yVtOuA

# **Image Classification Model Deployment**

## Profile

**Achmad Hadi Kurnia**

Link [Dicoding](https://www.dicoding.com/users/achmadhadikurnia)

## Kriteria
- [x] Dataset yang akan dipakai bebas, namun minimal memiliki 1000 buah gambar.
- [x] Dataset tidak pernah digunakan pada submission kelas machine learning sebelumnya.
- [x] Dataset dibagi menjadi 80% train set dan 20% test set.
- [x] Model harus menggunakan model sequential.
- [x] Model harus menggunakan Conv2D Maxpooling Layer.
- [x] Akurasi pada training dan validation set minimal sebesar 80%.
- [x] Menggunakan Callback.
- [x] Membuat plot terhadap akurasi dan loss model.
- [x] Menulis kode untuk menyimpan model ke dalam format TF-Lite.

## Saran untuk Penilaian Lebih Tinggi
- [x] Dataset yang digunakan berisi lebih dari 2000 gambar.
- [x] Mengimplementasikan Callback.
- [x] Gambar-gambar pada dataset memiliki resolusi yang tidak seragam.

### 1. Setup Kebutuhan
"""

# Commented out IPython magic to ensure Python compatibility.
# Installing packages
print('\nInstalling packages')
!pip install -q kaggle
!pip install split-folders

# Impor libary
import os
import zipfile
import tensorflow as tf
import splitfolders as sf
import matplotlib.pyplot as plt

from google.colab import files
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications import Xception
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import GlobalAveragePooling2D
from tensorflow.keras.layers import Input
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import Flatten
from tensorflow.keras.layers import Dropout
from tensorflow.keras.layers import Dense
from PIL import Image

# %matplotlib inline

# Upload credential
print('\nUpload credential')
credential = files.upload()
!chmod 600 /content/kaggle.json

# Prepare dataset
print('\nDownloading dataset')
! KAGGLE_CONFIG_DIR=/content/ kaggle datasets download -d duttadebadri/image-classification
localZip = 'image-classification.zip'
zipRef = zipfile.ZipFile(localZip, 'r')
zipRef.extractall('image-classification')
zipRef.close()

"""### 2. Menyiapkan data"""

dataset_path = 'image-classification/images/images'

def delete_non_jpg_empty_files(directory_path):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)

            if (not file.lower().endswith('.jpg')) or (os.path.getsize(file_path) == 0):
                print(f"Deleting {file_path} as it's not a .jpg file or it's empty")
                os.remove(file_path)

print('Deleting non .jpg files')
delete_non_jpg_empty_files(dataset_path)

def list_dirs_and_files(directory_path):
    print('Folder and its number of files:')

    folders = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]
    total_files = 0
    total_folders = len(folders)

    for folder in folders:
        folder_path = os.path.join(directory_path, folder)
        files = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
        file_count = len(files)
        total_files += file_count
        print(f"{folder} [{file_count}] files")

    print(f"\nTotal files in all folders: {total_files}")
    print(f"Total folders (label): {total_folders}")

print('\nDirectory dataset info')
list_dirs_and_files(dataset_path)

def list_various_resolutions(directory):
    folders = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
    image_sizes = []

    for folder in folders:
        folder_path = os.path.join(directory, folder)
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                with Image.open(file_path) as image:
                    width, height = image.size
                    image_sizes.append(f'{width}x{height}')

    unique_sizes = set(image_sizes)
    first_size_unique = 8

    print(f'Size all images: {len(image_sizes)}')
    print(f'Size unique images: {len(unique_sizes)}')
    print(f'First {first_size_unique} unique images: {list(unique_sizes)[:first_size_unique]}')

print('\nList various resolutions')
list_various_resolutions(dataset_path)

image_dir = os.path.join('image-classification/image')

sf.ratio(
    dataset_path,
    output = image_dir,
    seed = None,
    ratio = (0.8, 0.2),
)

"""### 3. Modeling"""

train_dir = image_dir+'/train'
val_dir = image_dir+'/val'
label_size = len(os.listdir(val_dir))

train_datagen = ImageDataGenerator(
    rescale = 1./255,
    rotation_range = 45,
    width_shift_range = 0.2,
    height_shift_range = 0.2,
    shear_range = 0.2,
    zoom_range = 0.2,
    horizontal_flip = True,
    vertical_flip = True,
    fill_mode = 'nearest',
    validation_split = 0.2,
)

val_datagen = ImageDataGenerator(
    rescale = 1./255,
)

train_gen = train_datagen.flow_from_directory(
    train_dir,
    target_size = (150, 150),
    batch_size = 64,
    shuffle = True,
    color_mode = 'rgb',
    class_mode = 'categorical',
)

val_gen = val_datagen.flow_from_directory(
    val_dir,
    target_size = (150, 150),
    batch_size = 64,
    shuffle = True,
    color_mode = 'rgb',
    class_mode = 'categorical',
)

model = tf.keras.Sequential([
    tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(150, 150, 3)),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Conv2D(128, (3, 3), activation='relu'),
    tf.keras.layers.MaxPooling2D(2, 2),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(512, activation='relu'),
    tf.keras.layers.Dense(label_size, activation='softmax'),
])

learning_rate=0.001
optimizer = 'adam'
model.compile(
    loss = 'categorical_crossentropy',
    optimizer = optimizer,
    metrics = ['accuracy'],
)

print('\nModel summary')
model.summary()

class accuracyThresholdCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if logs.get('accuracy') >= 0.92 and logs.get('val_accuracy') >= 0.92:
            print("\nAccuracy has reached 92%!")
            self.model.stop_training = True

callbacks = accuracyThresholdCallback()

print('\nTraining process')
epoch_number = 64
history = model.fit(
    train_gen,
    epochs = epoch_number,
    steps_per_epoch = 16,
    validation_data = val_gen,
    validation_steps = 16,
    callbacks = [callbacks],
    verbose = 2,
)

"""## 4. Plot"""

train_accuracy = history.history['accuracy']
val_accuracy = history.history['val_accuracy']
train_loss = history.history['loss']
val_loss = history.history['val_loss']
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

# Plot accuracy
axes[0].plot(train_accuracy, label='Train Accuracy')
axes[0].plot(val_accuracy, label='Validation Accuracy')
axes[0].set_title('Model Accuracy')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('Accuracy')
axes[0].legend(loc='upper right')

# Plot loss
axes[1].plot(train_loss, label='Train Loss')
axes[1].plot(val_loss, label='Validation Loss')
axes[1].set_title('Model Lost')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('Loss')
axes[1].legend(loc='upper right')

plt.tight_layout()
plt.show()

"""## **Convert to TFLite**"""

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with tf.io.gfile.GFile("model.tflite", "wb") as f:
  f.write(tflite_model)