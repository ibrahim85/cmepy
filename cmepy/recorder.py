"""
CmeRecorder is a utility class for computation of measurements.
"""

import itertools
from cmepy.statistics import Distribution
from cmepy.measurement import Measurement
from cmepy.lazy_dict import LazyDict

def create(*targets):
    """
    create(*targets) -> cme_recorder
    """
    return CmeRecorder(*targets)

class CmeRecorder(object):
    """
    CmeRecorder is a utility class to compute common measurements,
    such as marginals, expected values, and standard deviations, from
    a given distribution p. 
    """
    
    def __init__(self, *targets):
        """
        Initialise CmeRecorder, optionally using the given sequence of targets.
        """
        object.__init__(self)
        
        self.times = []
        self.distributions = []
        self.transforms = {}
        self.measurements = LazyDict(self._update_measurement)
        
        for target in targets:
            self.add_target(*target)
    
    def add_target(self, *args):
        """
        rec.add_target(*targets)
        
        where each target has the form (variables[, transforms])
        """
        
        n_args = len(args)
        if n_args < 1:
            lament = 'add_target expected at least 1 argument, got %d'
            raise TypeError(lament % n_args)
        if n_args > 2:
            lament = 'add_target expected at most 2 arguments, got %d'
            raise TypeError(lament % n_args)
        
        variables = args[0]
        
        if n_args == 1:
            def f(dim):
                """
                default transform function, generated by recorder
                """
                return lambda state : (state[dim], )
            transforms = tuple(f(i) for i in xrange(len(variables)))
        else:
            def pre_star(f):
                """
                wrapped transform function, generated by recorder
                """
                return lambda state : (f(*state), )
            transforms = tuple(pre_star(f) for f in args[1])
        
        if len(variables) != len(transforms):
            raise ValueError('variables and transforms length mismatch')
        
        for var, transform in itertools.izip(variables, transforms):
            self.transforms[var] = transform
    
    def _update_measurement(self, var, measurement, member):
        """
        rec._update_measurement(var, measurement) -> updated_measurement
        """
        
        if not member:
            if var in self.transforms:
                transform = self.transforms[var]
            else:
                # attempt to parse var as a tuple of vars
                # and construct derived product transform if
                # successful
                product_t = [self.transforms[v] for v in var]
                def transform(state):
                    """
                    product transform function, generated by recorder
                    """
                    return sum((t(state) for t in product_t), ())
            measurement = Measurement(var, transform)
        start = len(measurement)
        end = len(self.times)
        for i in xrange(start, end):
            measurement.write(self.times[i], self.distributions[i])
        return measurement
        
    def write(self, t, p):
        """
        rec.write(t, p) : records measurements of time t and distribution p
        """
        
        if type(p) is not Distribution:
            p = Distribution(p)
        
        self.times.append(t)
        self.distributions.append(p)
    
    def __getitem__(self, item):
        return self.measurements[item]
    
def display_plots(rec, vars = None, statistics = None, title = None):
    """
    plot and display statistics from specified recorder measurement batch.
    
    Requires pylab (eg the matplotlib package) to be installed.
    """
    
    if statistics is None:
        statistics = ('expected_value', 'standard_deviation')
    if title is None:
        title = 'Results'
    if vars is None:
        vars = rec.transforms
    
    import pylab
    
    for statistic in statistics:
        pylab.figure()
        for var in vars:
            print 'display_plots : computing measurements for %s' % str(var)
            measurement = rec.measurements[var]
            pylab.plot(measurement.times,
                       measurement.get_statistic(statistic),
                       label = str(measurement.name))
        print 'display_plots : plotting statistic %s' % statistic
        pylab.legend()
        plot_title = ': '.join((title, str(statistic)))
        pylab.title(plot_title)
    pylab.show()
