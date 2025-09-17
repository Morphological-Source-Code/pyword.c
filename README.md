# pyword.c
pyword.c is a pythonic C&lt;->CPython harness with LSP-like features; an easy to-use python 3.12+ module for CICD and reflective/reflexive introspection of dynamic C libraries.

## install + run
(optional) virtual-env:
    `python -m venv .venv && source .venv/bin/activate`
finally:
`python -m pip install -e .`

```python
>>> import pyword
>>> w = pyword.PyWord()
>>> w.set_bytes(b"hello world")
>>> w.get_bytes()
b'hello world'
>>> len(w)
11

python -c "import pyword, sys; print(pyword.PyWord, file=sys.stderr)"
# <class 'pyword.PyWord'>
```

### CPythonification Guidance

1. **PyObject Manipulation**:
   - Access `PyObject` fields via `ctypes`:
     ```python
     frame = CPythonFrame.from_object("test")
     py_obj = py_object(frame)
     py_struct = PyObject.from_address(id(frame))
     ```
   - Manipulate `ob_refcnt` and `ob_type` for custom objects.

2. **Type System**:
   - Create `PyTypeObject` for `CPythonFrame`:
     ```python
     from ctypes import Structure, c_char_p, c_int
     class PyTypeObject(Structure):
         _fields_ = [("ob_base", PyObject), ("tp_name", c_char_p)]
     ```
   - Define methods via `PyMethodDef`.

3. **Reflexivity**:
   - Use `inspect` to extract and modify source code:
     ```python
     source = inspect.getsource(CPythonFrame)
     frame.value = source  # Store own source
     ```
   - Generate quines by recompiling source via `compile()`.

4. **Memory Management**:
   - Extend `PyWord` with a cache:
     ```python
     class PyWordCache:
         def __init__(self, capacity: int):
             self.cache = {}
             self.capacity = capacity
         def get(self, key: int) -> Optional[PyWord]:
             return self.cache.get(key)
         def put(self, key: int, word: PyWord):
             if len(self.cache) >= self.capacity:
                 self.cache.pop(next(iter(self.cache)))
             self.cache[key] = word
     ```
   - Use `PyMem_Malloc` for allocations.

5. **Resources**:
   - CPython Source: `Include/object.h`, `Objects/typeobject.c`.
   - C API Docs: https://docs.python.org/3/c-api/
   - Homoiconicity: Study Lisp/Scheme for inspiration.


### Future
LSP, CICD, after I build tests and bug test the existing bit/memoryview harness.
