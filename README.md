# pyword.c
pyword.c is a pythonic C&lt;->CPython harness with LSP-like features; an easy to-use python 3.12+ module for CICD and reflective/reflexive introspection of dynamic C libraries.

## install + run
python -m pip install .

```python
>>> import pyword
>>> w = pyword.PyWord()
>>> w.set_bytes(b"hello world")
>>> w.get_bytes()
b'hello world'
>>> len(w)
11
```

### Future
LSP, CICD, after I build tests and bug test the existing bit/memoryview harness.
