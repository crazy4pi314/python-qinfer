#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# test_utils.py: Tests helper functions in utils.py
##
# © 2017, Chris Ferrie (csferrie@gmail.com) and
#         Christopher Granade (cgranade@cgranade.com).
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     1. Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#     2. Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in the
#        documentation and/or other materials provided with the distribution.
#
#     3. Neither the name of the copyright holder nor the names of its
#        contributors may be used to endorse or promote products derived from
#        this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
##

## FEATURES ###################################################################

from __future__ import absolute_import
from __future__ import division # Ensures that a/b is always a float.

## IMPORTS ####################################################################

import warnings
import unittest

from scipy.linalg import sqrtm
import numpy as np
from numpy.testing import assert_equal, assert_almost_equal

from qinfer.tests.base_test import DerandomizedTestCase, MockModel, assert_warns

from qinfer.utils import in_ellipsoid, assert_sigfigs_equal, sqrtm_psd, to_simplex, from_simplex

## TESTS #####################################################################

class TestNumericTests(DerandomizedTestCase):

    def test_assert_sigfigs_equal(self):
        """
        Tests to make sure assert_sigfigs_equal
        only passes if the correct number of 
        significant figures match
        """

        # these are the same to 6 sigfigs
        assert_sigfigs_equal(
            np.array([3.141592]),
            np.array([3.141593]),
            6
        )
        # these are only the same to 5 sigfigs
        self.assertRaises(
            AssertionError,
            assert_sigfigs_equal,
            np.array([3.14159]),
            np.array([3.14158]),
            6
        )

        # these are the same to 3 sigfigs
        assert_sigfigs_equal(
            np.array([1729]),
            np.array([1728]),
            3
        )
        # these are only the same to 3 sigfigs
        self.assertRaises(
            AssertionError,
            assert_sigfigs_equal,
            np.array([1729]),
            np.array([1728]),
            4
        )


class TestEllipsoids(DerandomizedTestCase):

    def test_in_ellipsoid(self):
        
        # the semi-major axes are the square roots of the 
        # singular values, so 2 and 1 in this case.
        A = np.array([[4,0], [0,1]])
        c = np.array([0,1])

        # test with multiple inputs. account for numerical error at boundary.
        x = np.array([[10,5],[0,1],[0,2],[0,3],[2,1],[3,1],[0.5,1.5]])
        assert_equal(
            in_ellipsoid(x, A, c), 
            np.array([0, 1, 1, 0, 1, 0, 1],dtype=bool)
        )
        # test with single input
        assert(in_ellipsoid(c,A,c))

        # Random positive matrix and origin
        A = np.random.randn(5, 5)
        A = np.dot(A, A.T)
        c = np.random.randn(5)

        # Look along a couple of the semi-major axes
        U, s, _ = np.linalg.svd(A)
        x = np.vstack([
            c + 0.99 * np.sqrt(s[2]) * U[:,2],
            c + 1.01 * np.sqrt(s[2]) * U[:,2],
            c - 0.99 * np.sqrt(s[0]) * U[:,0],
            c - 1.01 * np.sqrt(s[0]) * U[:,0],
        ])
        assert_equal(
            in_ellipsoid(x, A, c), 
            np.array([1,0,1,0], dtype=bool)
        )

class TestLinearAlgebra(DerandomizedTestCase):
    def test_sqrtm_psd(self):
        # Construct Y = XX^T as a PSD matrix.
        X = np.random.random((5, 5))
        Y = np.dot(X, X.T)
        sqrt_Y = sqrtm_psd(Y, est_error=False)

        np.testing.assert_allclose(
            np.dot(sqrt_Y, sqrt_Y),
            Y
        )

        # Try again, but with a singular matrix.
        Y_singular = np.zeros((6, 6))
        Y_singular[:5, :5] = Y
        sqrt_Y_singular = sqrtm_psd(Y_singular, est_error=False)

        np.testing.assert_allclose(
            np.dot(sqrt_Y_singular, sqrt_Y_singular),
            Y_singular
        )

class TestSimplexTransforms(DerandomizedTestCase):
    """
    Tests to_simplex and from_simplex.
    """

    def test_to_simplex(self):

        y = np.random.random(size=(20,10,15))
        y[..., -1] = 0
        x = to_simplex(y)

        assert(x.shape == y.shape)
        assert(np.all(np.isfinite(x)))
        assert_almost_equal(np.sum(x, axis=-1), 1)

        y = np.random.random(size=(15,))
        y[..., -1] = 0
        x = to_simplex(y)

        assert(x.shape == y.shape)
        assert(np.all(np.isfinite(x)))
        assert_almost_equal(np.sum(x, axis=-1), 1)

    def test_from_simplex(self):

        x = np.abs(np.random.random(size=(20,10,15)))
        x = x / np.sum(x, axis=-1)[...,np.newaxis]
        y = from_simplex(x)

        assert(x.shape == y.shape)
        assert(np.all(np.isfinite(y)))
        assert(np.all(np.isreal(y)))
        assert_almost_equal(y[..., -1], 0)

        x = np.abs(np.random.random(size=(15,)))
        x = x / np.sum(x, axis=-1)[...,np.newaxis]
        y = from_simplex(x)

        assert(x.shape == y.shape)
        assert(np.all(np.isfinite(y)))
        assert(np.all(np.isreal(y)))
        assert_almost_equal(y[..., -1], 0)

    def test_inverses(self):

        y = np.random.random(size=(20,10,15))
        y[..., -1] = 0
        x = to_simplex(y)

        assert_almost_equal(from_simplex(x), y)

        x = np.abs(np.random.random(size=(20,10,15)))
        x = x / np.sum(x, axis=-1)[...,np.newaxis]
        y = from_simplex(x)

        assert_almost_equal(to_simplex(y), x)
