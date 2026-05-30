# -*- coding: utf-8 -*-

"""
有限状态机的树形封装，灵活性不如FSM但易于模块化
"""

from ...core.unreliable import Unreliable

def nodePathStr(paths):
    return ' -> '.join([node.name for node in paths])

class StateTree(Unreliable):
    def __init__(self, entityId):
        Unreliable.__init__(self)
        self.entityId = entityId
        # 根节点没有父节点
        self.root = StateNode('root')
        self.mapping = {}
        self._current = None
        self._finished = False
        self.stateTicks = 0

    def reset(self, clearMapping=False):
        self._current = None
        self._finished = True
        if clearMapping:
            self.mapping = {}

    def findNamedNode(self, name):
        return self.root.findNamedNode(name)

    def insertNode(self, node, parent=None):
        parent = parent or self.root
        parent.addChildren(node)
        return node
    
    def createNode(self, parent=None):
        node = StateNode()
        return self.insertNode(node, parent)

    def replaceNode(self, src, target):
        if not src:
            self.root.addChildren(target)
            return

        parent = src._parent
        if not parent:
            # 替换根节点
            self.root = target
            target._parent = None
            return
        # ensure we detach source and attach target properly
        parent.removeChild(src)
        parent.addChildren(target)

    def replaceNamedNode(self, name, target):
        src = self.findNamedNode(name)
        self.replaceNode(src, target)
    
    def _enterNode(self, node, previous):
        self._current = node
        # enter signature: (previous_node, tree)
        self._finished = False
        self.tryCall(node.enter, previous, self)

    def _exitNode(self, nextNode):
        if self._current is not None:
            # exit signature: (nextNode, tree)
            self.tryCall(self._current.exit, nextNode, self)
            self._finished = True
            self._current = None

    def switchNode(self, node):
        previous = self._current
        self._exitNode(node)
        self._enterNode(node, previous)
        self.stateTicks = 0

    def finishTasks(self):
        self._finished = True

    # Accessors / mutators (lower camelCase)
    def setRoot(self, node):
        self.root = node
        if node is not None:
            node._parent = None

    def getRoot(self):
        return self.root

    def setCurrent(self, node):
        self._current = node

    def getCurrent(self):
        return self._current

    def clearCurrent(self):
        self._current = None

    def setFinished(self, val):
        self._finished = bool(val)

    def isFinished(self):
        return bool(self._finished)

    def searchNode(self):
        """
        搜索下一个可以进入的叶子节点，返回最终节点和途径节点
        
        搜索算法：
        1. 如果当前节点是None或根节点，从根节点开始搜索第一个可以进入的叶子节点
        2. 如果当前节点是叶子节点需要切换：
           a. 首先搜索同父节点的兄弟节点（按children顺序）
           b. 如果找不到，向上到父节点，搜索父节点的其他子节点
           c. 继续向上直到根节点
        3. 搜索时按children数组顺序寻找可以进入的节点
           - 如果不是叶子节点，继续递归搜索其子节点
        
        Returns:
            如果找到: (finalNode, pathNodes) 元组，其中：
                - finalNode: 最终找到的叶子节点
                - pathNodes: 从当前节点到最终节点的途径节点列表（不包括当前节点，包括最终节点）
            如果搜索失败: None
        """
        if not self._finished:
            return None

        if self.root is None:
            return None
            
        # 如果当前没有节点，从根节点开始搜索第一个可以进入的叶子节点
        if self._current is None:
            result = self.searchLeafFromNodeWithPath(self.root)
            if result is None:
                return None
            finalNode, pathNodes = result
            return finalNode, pathNodes
            
        # 检查当前节点是否可以退出。如果当前节点是非叶子，我们仍然可
        # 以进入其子节点，因此只在需要离开当前叶子时检查。
        if self._current._isLeaf and not self._current.canExit(self):
            return None  # 当前叶子不能退出，搜索失败
            
        # 如果当前节点是叶子节点，尝试切换
        if self._current._isLeaf:
            result = self.searchNextLeafWithPath(self._current)
            if result is None:
                return None
            finalNode, pathNodes = result
            if finalNode is not None and finalNode.canEnter(self):
                return finalNode, pathNodes
            else:
                return None
        else:
            # 当前节点不是叶子节点，继续搜索其子节点中的叶子节点
            result = self.searchLeafFromNodeWithPath(self._current)
            if result is None:
                return None
            finalNode, pathNodes = result
            # pathNodes 从 startNode 开始，搜索自身是起点，我们需要去掉
            # 起始节点（当前节点），因为返回值应“不包括当前节点”。
            if pathNodes and pathNodes[0] is self._current:
                pathNodes = pathNodes[1:]
            return finalNode, pathNodes
        
    def searchLeafFromNodeWithPath(self, startNode):
        """从指定节点开始搜索第一个可以进入的叶子节点，返回节点和路径"""
        if startNode is None:
            return None
            
        # 使用栈进行深度优先搜索，保持children顺序，同时记录路径
        stack = [(startNode, [startNode])]  # (node, pathToNode)
        while stack:
            node, path = stack.pop(0)
            
            # 如果是叶子节点且可以进入，返回它和路径
            if node._isLeaf and node.canEnter(self):
                return node, path
            
            # 如果不是叶子节点，按顺序添加子节点到栈前
            # 这样会先搜索第一个子节点
            for i in range(len(node.children) - 1, -1, -1):
                child = node.children[i]
                if child.canEnter(self):
                    newPath = path + [child]
                    stack.insert(0, (child, newPath))
        # 没有找到叶子节点
        return None

    def searchNextLeafWithPath(self, currentNode):
        """搜索当前叶子节点的下一个叶子节点，返回节点和路径

        此方法不再只查看当前节点之后的兄弟，而是扫描父节点的所有
        子节点（除自身外），以便在任意位置都能找到可进入的叶子。
        保留向上回溯的步骤。

        额外注意：如果当前节点的父节点本身不可进入（canEnter 返回 False），
        那么从该父节点内部寻找下一个叶子是不合理的——退出当前分支后
        无法重新进入此父节点。此时应该从父节点的父节点开始重新搜索。
        """
        if currentNode is None or currentNode._parent is None:
            # 当前节点是根节点或没有父节点，从根节点开始搜索
            return self.searchLeafFromNodeWithPath(self.root)

        parent = currentNode._parent
        # 如果父节点无法进入，直接从grandparent开始上行搜索
        if not parent.canEnter(self):
            return self.searchUpwardWithPath(parent._parent, currentNode)

        # 搜索父节点所有孩子（除自身），按列表顺序
        for sibling in parent.children:
            if sibling is currentNode:
                continue
            result = self.findFirstEnterableLeafWithPath(sibling)
            if result is not None:
                leaf, path = result
                fullPath = [parent] + path if parent is not None else path
                return leaf, fullPath

        # 如果父级所有子节点都不能进入，则向上搜索
        return self.searchUpwardWithPath(parent, currentNode)
        
    def findFirstEnterableLeafWithPath(self, node, currentPath=None):
        """查找节点或其子节点中第一个可以进入的叶子节点，返回节点和路径"""
        if currentPath is None:
            currentPath = []
            
        if not node.canEnter(self):
            return None
            
        newPath = currentPath + [node]
        
        if node._isLeaf:
            return node, newPath
            
        # 递归搜索子节点
        for child in node.children:
            result = self.findFirstEnterableLeafWithPath(child, newPath)
            if result is not None:
                return result
                
        return None

    def searchUpwardWithPath(self, parent, originalNode):
        """向上搜索叶子节点，返回节点和路径

        Path 构建规则：返回的路径不包括 originalNode，
        但会包含向上访问过的父节点，以便执行时能够正确
        退出当前分支并进入新的分支。

        如果某个祖先节点不可进入，则不应将它包含在路径中，
        同时要继续向上寻找下一层可进入的祖先作为新的起点。
        """
        currentParent = parent
        upward_path = []  # ancestors from the original node upward (excluding original)

        while currentParent is not None:
            # 如果当前祖先本身不能进入，跳过它
            if not currentParent.canEnter(self):
                currentParent = currentParent._parent
                continue

            # 如果已经到达根节点，用根重新搜索，并把已有上行路径拼接上
            if currentParent._parent is None:
                result = self.searchLeafFromNodeWithPath(self.root)
                if result is None:
                    return None
                leaf, path = result
                fullPath = upward_path + path
                return leaf, fullPath

            grandparent = currentParent._parent
            parentIndex = grandparent.children.index(currentParent)

            # 搜索 parent 之后的兄弟节点
            for i in range(parentIndex + 1, len(grandparent.children)):
                sibling = grandparent.children[i]
                result = self.findFirstEnterableLeafWithPath(sibling)
                if result is not None:
                    leaf, path = result
                    # 构建完整路径：从原始节点的父链到祖父节点，再到目标叶子节点
                    fullPath = upward_path + [grandparent] + path
                    return leaf, fullPath

            # 继续向上，记录当前父节点以便在最终路径中使用
            upward_path.append(currentParent)
            currentParent = grandparent

        # 搜索结束仍然未找到
        return None
    
    def findAllActivatedStateNodes(self):
        """查找所有激活的节点，包括当前节点和所有父节点"""
        nodes = []
        node = self._current
        while node is not None:
            nodes.append(node)
            node = node._parent
        nodes.reverse()
        return nodes
    
    def execute(self):
        """
        执行状态树搜索并切换
        
        步骤：
        1. 调用searchNode搜索下一个叶子节点和路径
        2. 如果搜索成功，沿着路径依次切换节点
        3. 最终切换到目标叶子节点
        
        注意：searchNode已经验证了所有节点的canEnter和canExit条件，
        所以这里直接切换，不再重复检查。
        
        Returns:
            成功切换到的叶子节点，如果搜索失败则返回None
        """
        if self._current:
            # print self._current.name
            self.stateTicks += 1
            for node in self.findAllActivatedStateNodes():
                node.update(self)

        searchResult = self.searchNode()
        if searchResult is None:
            return  # 搜索失败
            
        _, path = searchResult

        for node in path:
            self.switchNode(node)

    def currentState(self):
        return self._current
    
    def currentStateName(self):
        return self._current.name if self._current else None


class StateNode:
    def __init__(self, name='unknown'):
        self.name = name
        self._parent = None
        self.children = []
        self._isLeaf = True
        self._ctx = {}

    def canEnter(self, tree):
        # type: (StateTree) -> bool
        return True

    def canExit(self, tree):
        # type: (StateTree) -> bool
        return True

    def enter(self, previous, tree):
        # type: (StateNode, StateTree) -> None
        pass

    def exit(self, next, tree):
        # type: (StateNode, StateTree) -> None
        pass

    def update(self, tree):
        # type: (StateTree) -> None
        pass

    def addChildren(self, *nodes):
        # 将孩子添加到本节点，同时维护父引用
        self._isLeaf = False
        for node in nodes:
            node._parent = self
            self.children.append(node)

    def removeChild(self, node):
        if node in self.children:
            self.children.remove(node)
            node._parent = None
            # 如果没有剩余子节点，则本节点成为叶子
            if not self.children:
                self._isLeaf = True

    def insert(self, index, node):
        node._parent = self
        self.children.insert(index, node)

    def replaceChild(self, oldNode, newNode):
        index = self.children.index(oldNode)
        self.children[index] = newNode
        newNode._parent = self
        oldNode._parent = None

    def findNamedNode(self, name):
        if self.name == name:
            return self
        for child in self.children:
            result = child.findNamedNode(name)
            if result is not None:
                return result
        return None
    
    def copy(self, deep=True):
        """返回当前节点的副本。

        如果 deep=True（默认），会递归复制所有子节点并将它们
        附加到新的副本上。父引用不会被复制；返回的节点是一个
        完全独立的树根。

        复制过程会保留节点的类和大多数实例属性，除了
        ``_parent`` 和 ``children`` 之外的字段都会直接拷贝。
        这一策略让子类中定义的自定义属性（如测试中的
        ``_can_enter``、``_can_exit``）也能被复制。
        """
        # 先创建一个同类型的新节点，传递名称以保证子类 __init__ 正常运行
        cls = self.__class__
        try:
            new = cls(self.name)
        except TypeError:
            # 如果子类构造函数参数与预期不符，直接调用无参再赋值
            new = cls()
            new.name = self.name

        # 复制除了 _parent/children 之外的所有属性
        for k, v in self.__dict__.items():
            if k in ('_parent', 'children'):
                continue
            setattr(new, k, v)

        # 断开新节点的父引用并重置孩子列表
        new._parent = None
        new.children = []
        new._isLeaf = self._isLeaf

        if deep:
            for child in self.children:
                # 递归复制子节点并加入到新节点
                child_copy = child.copy(deep=True)
                new.addChildren(child_copy)

        return new

    def setContext(self, k, v):
        self._ctx[k] = v

    def getContext(self, k):
        value = self._ctx.get(k)
        if value is not None:
            return value
        if self._parent is not None:
            return self._parent.getContext(k)
        return None
