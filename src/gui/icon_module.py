import threading
import time

import imgui

from utils.common_utils import timer
from PIL import Image
import os
import numpy as np
from utils import graphic_uitls
from gui.global_var import *


class IconManager:
    icons = {}
    @staticmethod
    def _init_icons(dark_mode=True):
        sub_folder = 'light' if dark_mode else 'dark'
        for foldername, subfolders, filenames in os.walk(rf"../textures/{sub_folder}/"):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                img = Image.open(file_path)
                img_array = np.array(img)
                texture_id = graphic_uitls.create_texture_from_array(img_array)
                file_name, file_extension = os.path.splitext(filename)
                IconManager.icons[file_name] = texture_id

    @staticmethod
    def set_mode(dark_mode):
        IconManager._init_icons(dark_mode)

    @staticmethod
    def imgui_icon(name, width=20, height=20):
        if name not in IconManager.icons.keys():
            return
        imgui.image(IconManager.icons[name], width, height)


class Spinner:
    SPIN_ANI_FRAME = 40  # frame per sec
    SPIN_TIME = 1  # sec
    mSpinImageArray = []

    mDarkMode = True
    mSpinStartTime = {}
    mSpinLastIdx = {}
    mSpinTextureId = {}
    mSpinThread = {}

    @staticmethod
    def init(dark_mode=True):
        Spinner.mDarkMode = dark_mode

        Spinner.mSpinImageArray = []
        original_image = Image.open(f"../textures/{'light' if dark_mode else 'dark'}/spinner.png")
        # 对图像进行旋转操作
        for i in range(Spinner.SPIN_ANI_FRAME):
            rotated_image = original_image.rotate(360 / Spinner.SPIN_ANI_FRAME * i, expand=False,
                                                  fillcolor=(0, 0, 0, 0))
            Spinner.mSpinImageArray.append(np.array(rotated_image))

    @staticmethod
    def set_mode(dark_mode):
        Spinner.init(dark_mode)

    @staticmethod
    def spinner(name, width=20, height=20):
        if name not in Spinner.mSpinStartTime:
            return
        if not Spinner.mSpinThread[name].is_alive():
            Spinner.end(name)
            return
        start_time = Spinner.mSpinStartTime[name]
        t = (time.time() - start_time) % Spinner.SPIN_TIME / Spinner.SPIN_TIME
        idx = int(t * Spinner.SPIN_ANI_FRAME)
        if idx != Spinner.mSpinLastIdx[name]:
            graphic_uitls.update_texture(Spinner.mSpinTextureId[name], Spinner.mSpinImageArray[idx])
            Spinner.mSpinLastIdx[name] = idx
        imgui.same_line()
        imgui.image(Spinner.mSpinTextureId[name], width * GLOBAL_SCALE, height * GLOBAL_SCALE)

    @staticmethod
    def start(name, target, args):
        Spinner.mSpinStartTime[name] = time.time()
        Spinner.mSpinLastIdx[name] = 0
        Spinner.mSpinTextureId[name] = graphic_uitls.create_texture_from_array(Spinner.mSpinImageArray[0])
        thread = threading.Thread(target=target, args=args)
        Spinner.mSpinThread[name] = thread
        thread.start()

    @staticmethod
    def end(name):
        Spinner.mSpinStartTime.pop(name)
        Spinner.mSpinLastIdx.pop(name)
        Spinner.mSpinTextureId.pop(name)
