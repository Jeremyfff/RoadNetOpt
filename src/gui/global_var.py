GLOBAL_SCALE = 1.25
INIT_WINDOW_WIDTH = 1920 * GLOBAL_SCALE
INIT_WINDOW_HEIGHT = 1080 * GLOBAL_SCALE
LEFT_WINDOW_WIDTH = 400 * GLOBAL_SCALE
BOTTOM_WINDOW_HEIGHT = 32 * GLOBAL_SCALE
FONT_SIZE = 16 * GLOBAL_SCALE
FONT_SCALING_FACTOR = 1
DEFAULT_IMAGE_BUTTON_WIDTH = 20 * GLOBAL_SCALE
DEFAULT_IMAGE_BUTTON_HEIGHT = 20 * GLOBAL_SCALE
DEFAULT_ICON_WIDTH = 16 * GLOBAL_SCALE
DEFAULT_ICON_HEIGHT = 16 * GLOBAL_SCALE





mTextureScale = 2
mChineseFont = None

mFirstLoop = True
mFrameTime = 0

mDxfWindowOpened = False
mInfoWindowOpened = True
mLoggingWindowOpened = False

mSelectedRoads = {}  # 被选中的道路 dict{uid:road}
mHoveringImageWindow = False
mHoveringInfoSubWindow = False
mHoveringMainTextureSubWindow = False
mHoveringDxfSubWindow = False

mShowingMainTextureWindow = False
mImageSize = (0, 0)
mMousePosInImage = (0, 0)

mAddNodeMode = False
mCurrentEditingRoad = None

