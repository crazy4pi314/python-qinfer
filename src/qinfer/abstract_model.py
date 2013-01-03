#!/usr/bin/python
# -*- coding: utf-8 -*-
##
# abstract_model.py: Abstract interfaces for models with different levels of
#     functionality.
##
# © 2012 Chris Ferrie (csferrie@gmail.com) and
#        Christopher E. Granade (cgranade@gmail.com)
#     
# This file is a part of the Qinfer project.
# Licensed under the AGPL version 3.
##
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

## IMPORTS ##

import abc
    # Python standard library package for specifying abstract classes.
import numpy as np
    
## CLASSES ##

class Simulatable(object):
    __metaclass__ = abc.ABCMeta # Needed in any class that has abstract methods.
    
    def __init__(self):
        self._sim_count = 0
        
    ## ABSTRACT PROPERTIES ##
    
    @abc.abstractproperty
    def n_modelparams(self):
        """
        Returns the number of real model parameters admitted by this model.
        
        This property is assumed by inference engines to be constant for
        the lifetime of a Model instance.
        """
        pass
        
    @abc.abstractproperty
    def expparams_dtype(self):
        """
        Returns the dtype of an experiment parameter array. For a
        model with single-parameter control, this will likely be a scalar dtype,
        such as ``"float64"``. More generally, this can be an example of a
        record type, such as ``[('time', 'float64'), ('axis', 'uint8')]``.
        
        This property is assumed by inference engines to be constant for
        the lifetime of a Model instance.
        """
        pass
        
    ## CONCRETE PROPERTIES ##
    
    @property
    def is_n_outcomes_constant(self):
        """
        Returns ``True`` if and only if the number of outcomes for each
        experiment is independent of the experiment being performed.
        
        This property is assumed by inference engines to be constant for
        the lifetime of a Simulatable instance.
        """
        return False       
    
    @property
    def sim_count(self):
        return self._sim_count
        
    
    ## ABSTRACT METHODS ##
    
    @abc.abstractmethod
    def n_outcomes(self, expparams):
        """
        Returns an array of dtype ``uint`` describing the number of outcomes
        for each experiment specified by ``expparams``.
        
        :param numpy.ndarray expparams: Array of experimental parameters. This
            array must be of dtype agreeing with the ``expparams_dtype``
            property.
        """
        pass
    
    @abc.abstractmethod
    def are_models_valid(self, modelparams):
        """
        Given a shape ``(n_models, n_modelparams)`` array of model parameters,
        returns a boolean array of shape ``(n_models)`` specifying whether
        each set of model parameters represents is valid under this model.
        """
        pass
        
    @abc.abstractmethod
    def simulate_experiment(self, modelparams, expparams, repeat=1):
        # TODO: document
        self._sim_count += modelparams.shape[0] * expparams.shape[0] * repeat

class Model(Simulatable):
    # TODO: now that Model is a subclass of Simulatable, Model may no longer
    #       be the best name. Maybe rename to SimulatableModel and
    #       ExplicitModel?
    
    ## INITIALIZERS ##
    def __init__(self):
        self._call_count = 0
    
    ## CONCRETE PROPERTIES ##
    
    @property
    def call_count(self):
        # TODO: document
        return self._call_count
    
    ## ABSTRACT METHODS ##
    
    @abc.abstractmethod
    def likelihood(self, outcomes, modelparams, expparams):
        # TODO: document
        
        # Count the number of times the inner-most loop is called.
        self._call_count += outcomes.shape[0] * modelparams.shape[0] * expparams.shape[0]
                
    ## CONCRETE METHODS ##
    # These methods depend on the abstract methods, and thus their behaviors
    # change in each inheriting class.
    
    def is_model_valid(self, modelparams):
        """
        Returns True if and only if the model parameters given are valid for
        this model.
        """
        return self.are_models_valid(modelparams[np.newaxis, :])[0]
    
    def simulate_experiment(self, modelparams, expparams, repeat=1):
        # NOTE: implements abstract method of Simulatable.
        # TODO: document
        
        # Call the superclass simulate_experiment, not recording the result.
        # This is used to count simulation calls.
        super(Model, self).simulate_experiment(modelparams, expparams, repeat)
        
        probabilities = self.likelihood(np.arange(self.n_outcomes(expparams)), modelparams, expparams)
        cdf = np.cumsum(probabilities)
        randnum = np.random.random((repeat, 1))
        
        outcomes = np.argmax(cdf > randnum, axis=1)
        return outcomes[0] if repeat==1 else outcomes
                
    ## STATIC METHODS ##
    # These methods are provided as a convienence to make it easier to write
    # simple models.
    
    @staticmethod
    def pr0_to_likelihood_array(outcomes, pr0):
        """
        Assuming a two-outcome measurement with probabilities given by the
        array ``pr0``, returns an array of the form expected to be returned by
        ``likelihood`` method.
        
        :param numpy.ndarray outcomes: Array of integers indexing outcomes.
        :param numpy.ndarray pr0: Array of shape ``(n_models, n_experiments)``
            describing the probability of obtaining outcome ``0`` from each
            set of model parameters and experiment parameters.
        """
        pr0 = pr0[np.newaxis, ...]
        return np.concatenate([
            pr0 if outcomes[idx] == 0 else 1 - pr0
            for idx in xrange(outcomes.shape[0])
            ]) 
        
class DifferentiableModel(Model):
    __metaclass__ = abc.ABCMeta # Needed in any class that has abstract methods.
    
    @abc.abstractmethod
    def grad_log_likelihood(self, outcome, modelparams, expparams):
        #TODO document
        pass
