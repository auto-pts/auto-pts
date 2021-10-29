from abc import ABC, abstractmethod


class IutCtl(ABC):

    @abstractmethod
    def __init__(self, args):
        pass

    @abstractmethod
    def start(self, test_case):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def reset(self):
        pass
