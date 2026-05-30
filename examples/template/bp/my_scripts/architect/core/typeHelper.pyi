from typing import TypeVar, overload, Any, List, Dict, Tuple, Callable

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

T1 = TypeVar("T1")
T2 = TypeVar("T2")
T3 = TypeVar("T3")
T4 = TypeVar("T4")


@overload
def castTo(val: Any, t: type[List[T]], e: type[T]) -> List[T]:...


@overload
def castTo(val: Any, t: type[Dict[K, V]], k: type[K], v: type[V]) -> Dict[K, V]:...


@overload
def castTo(val: Any, t: type[Tuple[T]], e: type[T]) -> Tuple[T]:...


@overload
def castTo(val: Any, t: type[Tuple[T1, T2]], e1: type[T1], e2: type[T2]) -> Tuple[T1, T2]:...


@overload
def castTo(val: Any, t: type[Tuple[T1, T2, T3]], e1: type[T1], e2: type[T2], e3: type[T3]) -> Tuple[T1, T2, T3]:...


@overload
def castTo(val: Any, t: type[Tuple[T1, T2, T3, T4]], e1: type[T1], e2: type[T2], e3: type[T3], e4: type[T4]) -> Tuple[T1, T2, T3, T4]:...


@overload
def castTo(val: Any, t: type[T]) -> T:...

