import time
import imgui
from typing import Callable, TypeVar

AnimationBody = TypeVar('AnimationBody', bound=Callable[[int], bool])


def blank_body(frame_idx: int) -> bool:
    _ = frame_idx
    return True


class Animation:
    def __init__(self, body_func: AnimationBody, reset_func: Callable = None, time_gap: float = 0.1):
        self.body_func: Callable = body_func
        self.reset_func: Callable = reset_func
        self.can_play: bool = False
        self.next_time: float = 0
        self.frame_idx: int = 0
        self.time_gap: float = time_gap

    def reset(self):
        self.can_play = False
        self.next_time = 0
        self.frame_idx = 0
        if self.reset_func is not None:
            self.reset_func()


    def start(self):
        self.can_play = True

    def step(self):
        self.can_play = True
        self.next_time = 0
        self.show()
        self.can_play = False

    def stop(self):
        self.can_play = False

    def show(self):
        if not self.can_play:
            return
        if time.time() < self.next_time:
            return

        end = self.body_func(self.frame_idx)
        if end:
            self.stop()
            print(f'动画结束')
            return
        self.next_time = time.time() + self.time_gap
        print(f'next time set to {self.next_time}, current {time.time()}')
        self.frame_idx += 1

    @staticmethod
    def blank():
        return Animation(blank_body)
