import numpy as np
from PIL import Image, ImageFilter
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def fig2array(fig: Figure = None) -> np.ndarray:
    if fig is None:
        fig = plt.gcf()
    fig.canvas.draw()
    buf = fig.canvas.buffer_rgba()
    shape = buf.shape
    return np.frombuffer(buf, dtype=np.uint8).reshape(shape)


def array2image(array: np.ndarray) -> Image:
    image = Image.fromarray(array)
    return image


def blur_image(image: Image, radius=3):
    blurred_image = image.filter(ImageFilter.GaussianBlur(radius=radius))
    return blurred_image
