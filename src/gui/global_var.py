from typing import Union
import os
import moderngl
import moderngl_window.integrations.imgui

GLOBAL_SCALE = 1
DARK_MODE = True
INIT_WINDOW_WIDTH = 1280 * GLOBAL_SCALE
INIT_WINDOW_HEIGHT = 720 * GLOBAL_SCALE
LEFT_WINDOW_WIDTH = 400 * GLOBAL_SCALE
BOTTOM_WINDOW_HEIGHT = 32 * GLOBAL_SCALE
FONT_SIZE = 16 * GLOBAL_SCALE
FONT_SCALING_FACTOR = 1
DEFAULT_IMAGE_BUTTON_WIDTH = 20 * GLOBAL_SCALE
DEFAULT_IMAGE_BUTTON_HEIGHT = 20 * GLOBAL_SCALE
DEFAULT_ICON_WIDTH = 16 * GLOBAL_SCALE
DEFAULT_ICON_HEIGHT = 16 * GLOBAL_SCALE
RESOURCE_DIR = os.path.abspath('../resources/')
LINE_WIDTH_SCALE = 2
print(f'RESOURCE_DIR = {RESOURCE_DIR}')

mModernglWindowRenderer: Union[moderngl_window.integrations.imgui.ModernglWindowRenderer, None] = None
mCtx: Union[moderngl.Context, None] = None
mWindowSize = (1280, 720)
mWindowEvent: Union[moderngl_window.WindowConfig, None] = None

mTextureScale: float = 1.0
mChineseFont = None

mFirstLoop = True
mTime = 0
mFrameTime = 0

mDxfWindowOpened = False
mInfoWindowOpened = True
mLoggingWindowOpened = False

mHoveringImageWindow = False
mHoveringInfoSubWindow = False
mHoveringMainTextureSubWindow = False
mHoveringDxfSubWindow = False

mShowingMainTextureWindow = False
mImageSize = (0, 0)  # 纹理大小
mMousePosInImage = (0, 0)  # 鼠标位置（纹理空间
mImageWindowInnerSize = (0, 0)  # 图像控件的大小（屏幕空间
mImageWindowInnerPos = (0, 0)  # 图片控件在窗口的绝对位置（屏幕空间

mSelectedRoads = {}  # 被选中的道路 dict{uid:road}
mCurrentEditingRoad = None
mAddNodeMode = False

mShift = False
mCtrl = False
mAlt = False
