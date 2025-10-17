#!/usr/bin/env -S uv run
# /* script
# requires-python = ">=3.14"
# dependencies = [
#     "uv==*.*",
# ]
# -*- coding: utf-8 -*-
#------------------------------
# 3.14 std libs **ONLY**      |
# Platform(s):                |
# Win11 (dev*, prod) *Sandbox |
# Ubuntu-22.04 (prod, staging)|
#------------------------------
# <https://github.com/Morphological-Source-Code/pyword.c>
# • MSC: Morphological Source Code © 2025 by Phovos
import ctypes
import math
import random
import hashlib

class FieldRegister(ctypes.Structure):
    _fields_ = [
        ("raw", ctypes.c_uint8),
    ]

    def __init__(self, raw: int = 0):
        super().__init__(raw & 0xFF)

    @property
    def C(self) -> int: return (self.raw >> 7) & 0x1
    @property
    def V(self) -> int: return (self.raw >> 4) & 0x7
    @property
    def T(self) -> int: return self.raw & 0xF

    def clone(self): return FieldRegister(self.raw)

    def xor(self, other: 'FieldRegister') -> 'FieldRegister':
        return FieldRegister(self.raw ^ other.raw)

    def __repr__(self):
        return f"<FR C:{self.C} V:{self.V:03b} T:{self.T:04b} raw:{self.raw:08b}>"

class ScratchArena:
    """Register-local coherent memory"""
    def __init__(self, size: int = 64):
        self.mem = (FieldRegister * size)()
        self.size = size
        self.head = 0

    def push(self, fr: FieldRegister):
        self.mem[self.head % self.size] = fr
        self.head += 1

    def get(self, idx: int) -> FieldRegister:
        return self.mem[idx % self.size].clone()

    def view(self):
        return [f.raw for f in self.mem[:min(self.head, self.size)]]

class VarianceOperator:
    """Covariant and Contravariant Operators"""
    def __init__(self, phase: int):
        self.phase = phase  # +1 for covariant, -1 for contravariant

    def __call__(self, fr: FieldRegister, arena: ScratchArena) -> FieldRegister:
        # derive morphic effect by affine XOR on local arena
        idx = (hash(fr.raw) ^ (self.phase & 0xFF)) % arena.size
        neighbor = arena.get(idx)
        entropy = (bin(fr.raw ^ neighbor.raw).count("1")) / 8.0

        # phase coupling: covariant flows forward (entropy increase),
        # contravariant flows backward (entropy reduction)
        delta = (entropy * self.phase)
        delta_bits = int(abs(delta) * 15) & 0xF

        new_T = (fr.T ^ delta_bits) & 0xF
        new_V = (fr.V + (self.phase & 0x3)) & 0x7
        new_C = (fr.C ^ (1 if self.phase < 0 else 0)) & 0x1

        new_raw = (new_C << 7) | (new_V << 4) | new_T
        new_fr = FieldRegister(new_raw)
        arena.push(new_fr)
        return new_fr

if __name__ == "__main__":
    arena = ScratchArena(size=8)

    # Seed registers
    fr0 = FieldRegister(0b10110010)
    fr1 = FieldRegister(0b01011001)
    arena.push(fr0)
    arena.push(fr1)

    covar = VarianceOperator(+1)
    contra = VarianceOperator(-1)

    print("Initial registers:")
    print(fr0, fr1)

    print("\nCovariant propagation:")
    fr_c = covar(fr0, arena)
    print(fr_c)

    print("\nContravariant propagation:")
    fr_x = contra(fr1, arena)
    print(fr_x)

    print("\nArena state (entropy field):")
    print(arena.view())
