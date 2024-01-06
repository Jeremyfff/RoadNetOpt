import logging
import matplotlib.pyplot as plt
from geo import Road
from utils import  RoadLevel, RoadState
import networkx as nx


def init_plt():
    fig, ax = plt.subplots()
    ax.set_frame_on(False)  # 没有边框
    ax.set_xticks([])  # 没有 x 轴坐标
    ax.set_yticks([])  # 没有 y 轴坐标
    ax.set_aspect('equal')  # 横纵轴比例相同
    fig.tight_layout()
    return fig, ax

Road.quick_roads()
fig, ax = init_plt()

G = Road.to_graph()
pos = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
edge_width = {}
# 遍历图中的每条边，根据 RoadLevel 属性来设置边的粗细
for u, v, data in G.edges(data=True):
    road_level = data['level']
    if road_level == RoadLevel.MAIN:
        edge_width[(u, v)] = 5
    elif road_level == RoadLevel.SECONDARY:
        edge_width[(u, v)] = 3
    else:
        edge_width[(u, v)] = 1
nx.draw_networkx(G,
                 ax=ax,
                 pos=pos,
                 width=[edge_width[e] for e in G.edges()],
                 with_labels=False,
                 node_size=10)  # 绘制图形
plt.show()  # 显示图形