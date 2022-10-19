#!/usr/bin/env python
# -*- coding: utf-8 -*-

import heapq
import numpy as np


def getRandomPatch(texture, block_size):
    h, w = texture.shape[:2]

    if h == block_size:
        i = 0
    else:
        i = np.random.randint(h - block_size)

    if w == block_size:
        j = 0
    else:
        j = np.random.randint(w - block_size)
    return texture[i:i + block_size, j:j + block_size]


def getL2OverlapDiffError(patch, block_size, overlap, result, y, x):
    error = 0
    if x > 0:
        left = patch[:, :overlap] - result[y:y + block_size, x:x + overlap]
        error += np.sum(left**2)

    if y > 0:
        up = patch[:overlap, :] - result[y:y + overlap, x:x + block_size]
        error += np.sum(up**2)

    if x > 0 and y > 0:
        corner = patch[:overlap, :overlap] - result[y:y + overlap,
                                                    x:x + overlap]
        error -= np.sum(corner**2)
    return error


def getRandomBestPatch(texture, block_size, overlap, result, y, x):
    h, w = texture.shape[:2]
    errors = np.zeros((h - block_size, w - block_size))

    for i in range(h - block_size):
        for j in range(w - block_size):
            patch = texture[i:i + block_size, j:j + block_size]
            errors[i, j] = getL2OverlapDiffError(patch, block_size, overlap,
                                                 result, y, x)

    if errors.shape[0] > 0 and errors.shape[1] > 0:
        i, j = np.unravel_index(np.argmin(errors), errors.shape)
    else:
        i, j = 0, 0
    return texture[i:i + block_size, j:j + block_size]


def getMinCutPath(errors):
    pq = [(error, [i]) for i, error in enumerate(errors[0])]
    heapq.heapify(pq)

    h, w = errors.shape
    seen = set()

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
    return path


def getMinCutPatch(patch, overlap, result, y, x):
    patch = patch.copy()
    dy, dx, _ = patch.shape
    minCut = np.zeros_like(patch, dtype=bool)

    if x > 0:
        left = patch[:, :overlap] - result[y:y + dy, x:x + overlap]
        leftL2 = np.sum(left**2, axis=2)
        for i, j in enumerate(getMinCutPath(leftL2)):
            minCut[i, :j] = True

    if y > 0:
        up = patch[:overlap, :] - result[y:y + overlap, x:x + dx]
        upL2 = np.sum(up**2, axis=2)
        for j, i in enumerate(getMinCutPath(upL2.T)):
            minCut[:i, j] = True

    np.copyto(patch, result[y:y + dy, x:x + dx], where=minCut)
    return patch
