import importlib
import inspect
import pkgutil

from atguigu.task.action.base import Action
from atguigu.task.action.builtin.action_listen import ActionListen
from atguigu.task.action.builtin.action_response import ActionResponse
from atguigu.task.action.registry import ActionRegistry
from atguigu.task.action.runner import ActionRunner


def register_builtin_actions(action_runner: ActionRunner):
    """
    注册内置的action：手动 register
    :param action_runner:
    :return:
    """
    action_listen = ActionListen()
    action_response = ActionResponse()
    action_runner.registry.register(action_listen)
    action_runner.registry.register(action_response)


def register_custom_action(action_runner: ActionRunner):
    """这里要动态读取这个custom文件，因为custom文件是可能会增加或者减少功能的"""
    # 获取custom包
    package = importlib.import_module("atguigu.task.action.custom")

    # 这个方法便利这个包下面所有的文件
    # 在path路径下找到前缀是prefix的所有模块, 迭代custom下的子包和模块
    for _, module_name, is_pkb in pkgutil.iter_modules(package.__path__,prefix=f"{package.__name__}." ):
        # 只处理模块，不处理包
        if is_pkb: # 如果是软件包
            continue
        # 拿到当前模块
        module = importlib.import_module(module_name)
        # 获取当前模块下的所有成员
        for _, clz in inspect.getmembers(module, inspect.isclass): # isclass：获取类成员
            # 只过滤Action的子类,也不要action
            if not issubclass(clz, Action) or clz is Action:
                continue
            if clz.__module__ != module.__name__:
                continue
            # 将当前的obj注册到注册表
            action_runner.registry.register(clz())

def build_action_runner() -> ActionRunner:

    #初始化ActionRunner
    action_runner = ActionRunner(ActionRegistry())
    # 注册内置action
    register_builtin_actions(action_runner)
    # 注册自定义action
    register_custom_action(action_runner)

    return action_runner
