#ifndef PYWORD_H
#define PYWORD_H

#include <Python.h>
#include <stdint.h>

#define PYWORD_SIZE 64

/* Plain C object */
typedef struct {
    uint8_t data[PYWORD_SIZE];
    uint8_t len;          /* bytes in use (0..64) */
} PyWord;

/* C helpers */
static inline void pyword_set(PyWord *w, const uint8_t *src, uint8_t n) {
    n = n > PYWORD_SIZE ? PYWORD_SIZE : n;
    memcpy(w->data, src, n);
    w->len = n;
}
static inline const uint8_t *pyword_bytes(const PyWord *w) { return w->data; }
static inline uint8_t pyword_len(const PyWord *w) { return w->len; }

#endif
