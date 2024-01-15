import pygame

# 初始化pygame
pygame.init()

# 设置窗口尺寸
width, height = 800, 600
size = (width, height)

# 创建窗口
screen = pygame.display.set_mode(size)

# 设置窗口标题
pygame.display.set_caption("My Pygame Window")

# 游戏循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 在窗口上绘制内容
    screen.fill((255, 255, 255))  # 填充白色背景
    pygame.display.flip()  # 更新屏幕

# 退出pygame
pygame.quit()