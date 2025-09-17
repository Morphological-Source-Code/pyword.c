#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "pyword.h"

/* Python object wrapper */
typedef struct {
    PyObject_HEAD
    PyWord word;
} PyWordObject;

/* ----- constructors / destructors ----- */
static PyObject *
pyword_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyWordObject *self = (PyWordObject *)type->tp_alloc(type, 0);
    if (self) {
        self->word.len = 0;          /* start empty */
    }
    return (PyObject *)self;
}

static void
pyword_dealloc(PyWordObject *self)
{
    Py_TYPE(self)->tp_free((PyObject *)self);
}

/* ----- methods ----- */
PyDoc_STRVAR(pyword_set_bytes_doc,
"set_bytes(data) -> None\n"
"Copy *data* (bytes-like) into the PyWord buffer (truncated to 64 B).");
static PyObject *
pyword_set_bytes(PyWordObject *self, PyObject *obj)
{
    Py_buffer view;
    if (PyObject_GetBuffer(obj, &view, PyBUF_SIMPLE) < 0)
        return NULL;

    uint8_t n = view.len > PYWORD_SIZE ? PYWORD_SIZE : view.len;
    memcpy(self->word.data, view.buf, n);
    self->word.len = n;

    PyBuffer_Release(&view);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(pyword_get_bytes_doc,
"get_bytes() -> bytes\n"
"Return the current buffer as a Python bytes object.");
static PyObject *
pyword_get_bytes(PyWordObject *self)
{
    return PyBytes_FromStringAndSize((char *)self->word.data, self->word.len);
}

PyDoc_STRVAR(pyword_len_doc,
"__len__() -> int\n"
"Number of bytes currently stored (0..64).");
static Py_ssize_t
pyword_len(PyWordObject *self)
{
    return self->word.len;
}

static PyMethodDef pyword_methods[] = {
    {"set_bytes", (PyCFunction)pyword_set_bytes, METH_O, pyword_set_bytes_doc},
    {"get_bytes", (PyCFunction)pyword_get_bytes, METH_NOARGS, pyword_get_bytes_doc},
    {NULL, NULL}   /* sentinel */
};

static PyTypeObject PyWordType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name      = "pyword.PyWord",
    .tp_doc       = "64-byte opaque blob with Python buffer protocol",
    .tp_basicsize = sizeof(PyWordObject),
    .tp_flags     = Py_TPFLAGS_DEFAULT,
    .tp_new       = pyword_new,
    .tp_dealloc   = (destructor)pyword_dealloc,
    .tp_methods   = pyword_methods,
    .tp_as_sequence = NULL,        /* no sequence protocol */
    .tp_as_mapping = NULL,
    .tp_as_buffer = NULL,          /* add later; buffer protocol */
};

/* ---------- module ---------- */
static struct PyModuleDef pywordmodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "pyword",
    .m_doc  = "Minimal PyWord C extension",
    .m_size = -1,
};

PyMODINIT_FUNC
PyInit_pyword(void)
{
    PyObject *m;

    if (PyType_Ready(&PyWordType) < 0)
        return NULL;

    m = PyModule_Create(&pywordmodule);
    if (m == NULL)
        return NULL;

    Py_INCREF(&PyWordType);
    if (PyModule_AddObject(m, "PyWord", (PyObject *)&PyWordType) < 0) {
        Py_DECREF(&PyWordType);
        Py_DECREF(m);
        return NULL;
    }
    return m;
}
