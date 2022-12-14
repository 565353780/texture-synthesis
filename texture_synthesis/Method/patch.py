#!/usr/bin/env python
# -*- coding: utf-8 -*-

import heapq
import numpy as np

from texture_synthesis.Method.render import renderMinCutPatch


def getRandomPatch(texture, block_size):
    h, w = texture.shape[:2]

    if h == block_size[1]:
        i = 0
    else:
        i = np.random.randint(h - block_size[1])

    if w == block_size[0]:
        j = 0
    else:
        j = np.random.randint(w - block_size[0])
    return texture[i:i + block_size[1], j:j + block_size[0]]


def getL2OverlapDiffError(patch, block_size, overlap, result, y, x):
    error = 0
    if x > 0:
        left = patch[:, :overlap[0]] - result[y:y + block_size[1],
                                              x:x + overlap[0]]
        error += np.sum(left**2)

    if y > 0:
        up = patch[:overlap[1], :] - result[y:y + overlap[1],
                                            x:x + block_size[0]]
        error += np.sum(up**2)

    if x > 0 and y > 0:
        corner = patch[:overlap[1], :overlap[0]] - result[y:y + overlap[1],
                                                          x:x + overlap[0]]
        error -= np.sum(corner**2)
    return error


def getRandomBestPatch(texture, block_size, overlap, result, y, x):
    h, w = texture.shape[:2]
    errors = np.zeros((h - block_size[1], w - block_size[0]))

    for i in range(h - block_size[1]):
        for j in range(w - block_size[0]):
            patch = texture[i:i + block_size[1], j:j + block_size[0]]
            errors[i, j] = getL2OverlapDiffError(patch, block_size, overlap,
                                                 result, y, x)

    if errors.shape[0] > 0 and errors.shape[1] > 0:
        i, j = np.unravel_index(np.argmin(errors), errors.shape)
    else:
        i, j = 0, 0
    return texture[i:i + block_size[1], j:j + block_size[0]]


def getMinCutPath(errors):
    pq = [(error, [i]) for i, error in enumerate(errors[0])]
    heapq.heapify(pq)

    h, w = errors.shape
    seen = set()

    error = float('inf')
    path = None
    while pq:
        error, path = heapq.heappop(pq)
        curDepth = len(path)
        curIndex = path[-1]

        if curDepth == h:
            break

        for delta in -1, 0, 1:
            nextIndex = curIndex + delta

            if 0 <= nextIndex < w:
                if (curDepth, nextIndex) not in seen:
                    cumError = error + errors[curDepth, nextIndex]
                    heapq.heappush(pq, (cumError, path + [nextIndex]))
                    seen.add((curDepth, nextIndex))
    return path, error


def getMinCutPatch(patch, overlap, result, y, x):
    patch = patch.copy()
    dy, dx, _ = patch.shape
    minCut = np.zeros_like(patch, dtype=bool)

    error = 0
    if x > 0:
        left = patch[:, :overlap[0]] - result[y:y + dy, x:x + overlap[0]]
        left_abs = np.absolute(left)
        leftL2 = np.sum(left_abs**2, axis=2)
        path, x_error = getMinCutPath(leftL2)
        for i, j in enumerate(path):
            minCut[i, :j] = True
        error += x_error

    if y > 0:
        up = patch[:overlap[1], :] - result[y:y + overlap[1], x:x + dx]
        up_abs = np.absolute(up)
        upL2 = np.sum(up_abs**2, axis=2)
        path, y_error = getMinCutPath(upL2.T)
        for j, i in enumerate(path):
            minCut[:i, j] = True
        error += y_error

    np.copyto(patch, result[y:y + dy, x:x + dx], where=minCut)
    return patch, error
