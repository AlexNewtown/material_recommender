import os
import tempfile

import bpy
from bpy.props import CollectionProperty, FloatVectorProperty
from bpy.props import IntProperty, StringProperty
from bpy.types import PropertyGroup
import numpy as np

from . frame_id import FrameIdGroup


class MaterialData(PropertyGroup):

    id: StringProperty(
        name='Material ID',
        description='Unique id for this generated material',
    )

    frames_ids: CollectionProperty(
        type=FrameIdGroup,
        name='Frames IDs',
        description='IDs of the frames of the generated material for ' +
                    'retrieval from bpy.data.images or textures'
    )

    preview_frame_index: IntProperty(
        name='Previewed Frame Index',
        description='Remebers which frame is previewed'
    )

    rating: IntProperty(
        name='Rating',
        description='The rating given for a specific material. If given ' +
                    'a high rating, similar materials will be recommended',
        default=0,
        min=0,
        max=10
    )

    shader_values: FloatVectorProperty(
        name='Shader Values',
        description='Values for shader to render the material',
        size=20,
        precision=8
    )

    @property
    def current_frame_texture(self):
        return self.frame_texture(self.preview_frame_index)

    def frame_texture(self, frame_index):
        ''' Utility function to get the texture of a frame. '''
        return bpy.data.textures[self.frames_ids[frame_index].id]

    def frame_image(self, frame_index):
        ''' Utility function to get the image of a frame. '''
        return bpy.data.images[self.frames_ids[frame_index].id]

    def load_from_folder(self, path, frames_count=1, prefix='', extension=''):
        ''' prefix + "frame" + str(i).zfill(4) + extension '''
        for i in range(0, frames_count):
            file_name = prefix + "frame" + str(i).zfill(4) + extension
            self.frames_ids.add()
            self.frames_ids[-1].id = file_name

            bpy.data.images.load(os.path.join(path, file_name))
            bpy.data.textures.new(name=file_name, type='IMAGE')
            bpy.data.textures[file_name].image = bpy.data.images[file_name]

    def load_from_memory(self, frames):
        frames = frames.reshape(25, 200, 200, 3)
        for i in range(frames.shape[0]):
            # Preparing current frame
            frame = frames[i]
            height, width, _ = frame.shape
            alpha_channel = np.full((height, width, 1), 255)
            frame = np.concatenate((frame, alpha_channel), axis=2)
            frame = frame[::-1].flatten()

            # Adding the id
            frame_id = self.id + "_frame" + str(i).zfill(4)
            self.frames_ids.add()
            self.frames_ids[-1].id = frame_id

            # Loading it in bpy.data
            frame_image = bpy.data.images.new(
                frame_id,
                width=width,
                height=height,
                alpha=True,
                float_buffer=False
            )
            frame_texture = bpy.data.textures.new(
                name=frame_id,
                type='IMAGE'
            )
            frame_image.pixels = frame
            frame_texture.image = frame_image

    def save_to_disk(self, path='', file_format='PNG'):
        if path == '':
            path = tempfile.gettempdir()
            path = os.path.join(path, 'material_recommender')
            if not os.path.isdir(path):
                os.mkdir(path)

        frames_names = []
        for i in range(len(self.frames_ids)):
            frame = self.frame_image(i)
            frame.file_format = file_format
            file_name = 'frame' + str(i).zfill(4) + '.' + file_format.lower()
            frame_path = os.path.join(path, file_name)
            frames_names.append(file_name)
            if os.path.isfile(frame_path):
                os.remove(frame_path)
            frame.save_render(frame_path)
        return (path, frames_names)

    def clear_from_memory(self):
        for frame_id_prop in self.frames_ids:
            frame_id = frame_id_prop.id
            texture = bpy.data.textures[frame_id]
            bpy.data.textures.remove(texture)

            image = bpy.data.images[frame_id]
            bpy.data.images.remove(image)
