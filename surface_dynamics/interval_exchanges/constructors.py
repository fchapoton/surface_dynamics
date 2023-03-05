r"""
Interval exchange transformations

This library is designed for the usage and manipulation of interval
exchange transformations and linear involutions. It defines specialized
types of permutation (constructed using :func:`Permutation`) some
associated graph (constructed using ?) and some maps
of intervals (constructed using :func:`IntervalExchangeTransformation`).


EXAMPLES::

    sage: from surface_dynamics import *

Creation of an interval exchange transformation (iet)::

    sage: T = iet.IntervalExchangeTransformation(('a b','b a'),(sqrt(2),1))
    sage: T
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    a b
    b a

It can also be initialized using permutation (group theoritic ones)::

    sage: p = Permutation([3,2,1])
    sage: T = iet.IntervalExchangeTransformation(p, [1/3,2/3,1])
    sage: T
    Interval exchange transformation of [0, 2[ with permutation
    1 2 3
    3 2 1


As the iet's are functions, you can compose and invert them::

    sage: T = iet.IntervalExchangeTransformation(('a b','b a'),(sqrt(2),1))
    sage: T*T
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    aa ab ba
    ab ba aa
    sage: S = T.inverse()
    sage: S
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    b a
    a b
    sage: S * T
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    aa bb
    aa bb
    sage: (S * T).is_identity()
    True
    sage: T * S
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    bb aa
    bb aa
    sage: (T * S).is_identity()
    True

For the manipulation of permutations of iet, there are special types provided by
this module. All of them can be constructed using the constructor
iet.Permutation. For the creation of labelled permutations of interval exchange
transformation::

    sage: p1 =  iet.Permutation('a b c', 'c b a')
    sage: p1
    a b c
    c b a

They can be used for initialization of an iet::

    sage: p = iet.Permutation('a b', 'b a')
    sage: T = iet.IntervalExchangeTransformation(p, [1,sqrt(2)])
    sage: T
    Interval exchange transformation of [0, sqrt(2) + 1[ with permutation
    a b
    b a

You can also, create labelled permutations of linear involutions::

    sage: p = iet.GeneralizedPermutation('a a b', 'b c c')
    sage: p
    a a b
    b c c

By default, the permutations are labelled (it means that the labels are
important and (a b / b a) differs from (b a / a b)). It sometimes useful to deal
with reduced permutations for which the order does not import::

    sage: p = iet.Permutation('a b c', 'c b a', reduced = True)
    sage: p
    a b c
    c b a

Permutations with flips::

    sage: p1 = iet.Permutation('a b c', 'c b a', flips = ['a','c'])
    sage: p1
    -a  b -c
    -c  b -a

Creation of Rauzy diagrams::

    sage: r = iet.RauzyDiagram('a b c', 'c b a')

Reduced Rauzy diagrams are constructed using the same arguments than for
permutations::

    sage: r = iet.RauzyDiagram('a b b','c c a')
    sage: r_red = iet.RauzyDiagram('a b b','c c a',reduced=True)
    sage: r.cardinality()
    12
    sage: r_red.cardinality()
    4

By default, Rauzy diagram are generated by induction on the right. You can use
several options to enlarge (or restrict) the diagram (try help(iet.RauzyDiagram) for
more precisions)::

    sage: r1 = iet.RauzyDiagram('a b c','c b a',right_induction=True)
    sage: r2 = iet.RauzyDiagram('a b c','c b a',left_right_inversion=True)

You can consider self similar iet using path in Rauzy diagrams and eigenvectors
of the corresponding matrix::

    sage: p = iet.Permutation("a b c d", "d c b a")
    sage: d = p.rauzy_diagram()
    sage: g = d.path(p, 't', 't', 'b', 't', 'b', 'b', 't', 'b')
    sage: g
    Path of length 8 in a Rauzy diagram
    sage: g.is_loop()
    True
    sage: g.is_full()
    True
    sage: m = g.matrix()
    sage: v = m.eigenvectors_right()[-1][1][0]
    sage: T1 = iet.IntervalExchangeTransformation(p, v)
    sage: T2 = T1.rauzy_move(iterations=8)
    sage: T1.normalize(1) == T2.normalize(1)
    True

AUTHORS:

- Vincent Delecroix (2009-09-29): initial version

"""
# ****************************************************************************
#       Copyright (C) 2019-2021 Vincent Delecroix <20100.delecroix@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  https://www.gnu.org/licenses/
# ****************************************************************************

from __future__ import print_function, absolute_import
from six.moves import range

from sage.combinat.words.alphabet import Alphabet
from sage.rings.infinity import Infinity
from sage.misc.decorators import rename_keyword


def _two_lists(arg1, arg2):
    r"""
    Try to return the input as a list of two lists

    INPUT:

    - ``a`` - either a string, one or two lists, one or two tuples

    OUTPUT:

    -- two lists

    TESTS::

        sage: from surface_dynamics.interval_exchanges.constructors import _two_lists

        sage: _two_lists(('a1 a2','b1 b2'), None)
        [['a1', 'a2'], ['b1', 'b2']]
        sage: _two_lists('a1 a2\nb1 b2', None)
        [['a1', 'a2'], ['b1', 'b2']]
        sage: _two_lists(['a b','c'], None)
        [['a', 'b'], ['c']]

    Make sure that tuples are properly converted::

        sage: _two_lists(((0, 1), (1, 0)), None)
        [[0, 1], [1, 0]]
        sage: _two_lists((0, 1), (1, 0))
        [[0, 1], [1, 0]]

    ValueError or TypeError are raised with invalid arguments::

        sage: _two_lists('a b', None)
        Traceback (most recent call last):
        ...
        ValueError: the chain must contain two lines
        sage: _two_lists('a b\nc d\ne f', None)
        Traceback (most recent call last):
        ...
        ValueError: the chain must contain two lines
        sage: _two_lists(1, 1)
        Traceback (most recent call last):
        ...
        TypeError: argument not accepted
    """
    from sage.combinat.permutation import Permutation as CombinatPermutation
    from sage.groups.perm_gps.permgroup_element import PermutationGroupElement

    if arg2 is None:
        if isinstance(arg1, str):
            t = arg1.split('\n')
            if len(t) != 2:
                raise ValueError("the chain must contain two lines")
            return [t[0].split(), t[1].split()]

        elif isinstance(arg1, CombinatPermutation):
            return [list(range(1, len(arg1) + 1)), list(arg1)]

        elif isinstance(arg1, PermutationGroupElement):
            dom = list(arg1.parent().domain())
            return [dom, [arg1(i) for i in dom]]

        elif isinstance(arg1, (tuple, list)):
            try:
                t = CombinatPermutation(arg1)
            except Exception:
                if len(arg1) != 2:
                    raise ValueError('argument not accepted')
                arg1, arg2 = arg1
            else:
                return [list(range(1, len(t) + 1)), list(t)]

    if arg2 is None:
        raise ValueError("argument can not be split into two parts")

    res = []
    for a in (arg1, arg2):
        if isinstance(a, (tuple, list)):
            res.append(list(a))
        elif isinstance(a, str):
            res.append(a.split())
        else:
            raise TypeError('argument not accepted')

    return res


def Permutation(arg1, arg2=None, reduced=None, flips=None, alphabet=None):
    r"""
    Returns a permutation of an interval exchange transformation.

    Those permutations are the combinatoric part of an interval exchange
    transformation (IET). The combinatorial study of those objects starts with
    Gerard Rauzy [Rau80]_ and William Veech [Vee78]_.

    The combinatoric part of interval exchange transformation can be taken
    independently from its dynamical origin. It has an important link with
    strata of Abelian differential (see ?)

    INPUT:

    - ``intervals`` - string, two strings, list, tuples that can be converted to
      two lists

    - ``reduced`` - boolean (default: False) specifies reduction. False means
      labelled permutation and True means reduced permutation.

    - ``flips`` -  iterable (default: None) the letters which correspond to
      flipped intervals.

    - ``alphabet`` - (optional)

    OUTPUT:

    permutation -- the output type depends of the data.

    EXAMPLES::

        sage: from surface_dynamics import *

    Creation of labelled permutations ::

        sage: iet.Permutation('a b c d','d c b a')
        a b c d
        d c b a
        sage: iet.Permutation([[0,1,2,3],[2,1,3,0]])
        0 1 2 3
        2 1 3 0
        sage: iet.Permutation([0, 'A', 'B', 1], ['B', 0, 1, 'A'])
        0 A B 1
        B 0 1 A

    Creation of reduced permutations::

        sage: iet.Permutation('a b c', 'c b a', reduced = True)
        a b c
        c b a
        sage: iet.Permutation([0, 1, 2, 3], [1, 3, 0, 2], reduced=True)
        0 1 2 3
        1 3 0 2
        sage: iet.Permutation([2,1], reduced=True)
        1 2
        2 1

    Managing the alphabet: two labelled permutations with different (ordered)
    alphabet but with the same labels are different::

        sage: p = iet.Permutation('a b','b a', alphabet='ab')
        sage: q = iet.Permutation('a b','b a', alphabet='ba')
        sage: str(p) == str(q)
        True
        sage: p == q
        False
        sage: p.rauzy_move_matrix('top')
        [1 0]
        [1 1]
        sage: q.rauzy_move_matrix('top')
        [1 1]
        [0 1]

    For reduced permutations, the alphabet does not play any role excepted for
    printing the object::

        sage: p = iet.Permutation('a b c','c b a', reduced=True)
        sage: q = iet.Permutation([0,1,2],[2,1,0], reduced=True)
        sage: p == q
        True

    Creation of flipped permutations::

        sage: iet.Permutation('a b c', 'c b a', flips=['a','b'])
        -a -b  c
         c -b -a
        sage: iet.Permutation('a b c', 'c b a', flips='ab', reduced=True)
        -a -b  c
         c -b -a

    TESTS::

        sage: type(iet.Permutation('a b c', 'c b a', reduced=True))
        <class 'surface_dynamics.interval_exchanges.reduced.ReducedPermutationIET'>
        sage: type(iet.Permutation('a b c', 'c b a', reduced=False))
        <class 'surface_dynamics.interval_exchanges.labelled.LabelledPermutationIET'>
        sage: type(iet.Permutation('a b c', 'c b a', reduced=True, flips=['a','b']))
        <class 'surface_dynamics.interval_exchanges.reduced.FlippedReducedPermutationIET'>
        sage: type(iet.Permutation('a b c', 'c b a', reduced=False, flips=['a','b']))
        <class 'surface_dynamics.interval_exchanges.labelled.FlippedLabelledPermutationIET'>

        sage: p = iet.Permutation(('a b c','c b a'))
        sage: iet.Permutation(p) == p
        True
        sage: q = iet.Permutation(p, reduced=True)
        sage: q == p
        False
        sage: q == p.reduced()
        True

        sage: p = iet.Permutation('a', 'a', flips='a', reduced=True)
        sage: iet.Permutation(p) == p
        True

        sage: p = iet.Permutation('a b c','c b a',flips='a')
        sage: iet.Permutation(p) == p
        True
        sage: iet.Permutation(p, reduced=True) == p.reduced()
        True

        sage: p = iet.Permutation('a b c','c b a',reduced=True)
        sage: iet.Permutation(p) == p
        True
    """
    if arg2 is None:
        from .template import Permutation as Permutation_class
        if isinstance(arg1, Permutation_class):
            return Permutation(
                arg1.list(),
                reduced=(arg1._labels is None) if reduced is None else reduced,
                flips=arg1.flips() if flips is None else flips,
                alphabet=arg1.alphabet() if alphabet is None else alphabet)

    if reduced is None:
        reduced = False

    a = _two_lists(arg1, arg2)

    l = a[0] + a[1]
    letters = set(l)

    if flips is not None:
        # make it so that no flip is equivalent to not specifying the flips
        if not flips:
            flips = None
        else:
            for letter in flips:
                if letter not in letters:
                    raise ValueError("flips contains not valid letters")

    for letter in letters:
        if a[0].count(letter) != 1 or a[1].count(letter) != 1:
            raise ValueError("letters must appear once in each interval")

    if reduced:
        if flips is None:
            from .reduced import ReducedPermutationIET as cls
        else:
            from .reduced import FlippedReducedPermutationIET as cls
    else:
        if flips is None:
            from .labelled import LabelledPermutationIET as cls
        else:
            from .labelled import FlippedLabelledPermutationIET as cls

    return cls(a, alphabet=alphabet, reduced=reduced, flips=flips)


def GeneralizedPermutation(arg1, arg2=None, reduced=None, flips=None, alphabet=None):
    r"""
    Returns a permutation of an interval exchange transformation.

    Those permutations are the combinatoric part of linear involutions and were
    introduced by Danthony-Nogueira [DanNog90]_ (the flipped version is also
    considered in [Nog89]_). The full combinatoric study and precise links with
    strata of quadratic differentials was achieved few years later by
    Boissy-Lanneau [BoiLan09]_.

    INPUT:

    - ``intervals`` - strings, list, tuples

    - ``reduced`` - boolean (default: False) specifies reduction. False means
      labelled permutation and True means reduced permutation.

    - ``flips`` -  iterable (default: None) the letters which correspond to
      flipped intervals.

    OUTPUT:

    generalized permutation -- the output type depends on the data.

    EXAMPLES::

        sage: from surface_dynamics import *

    Creation of labelled generalized permutations::

        sage: iet.GeneralizedPermutation('a b b','c c a')
        a b b
        c c a
        sage: iet.GeneralizedPermutation('a a','b b c c')
        a a
        b b c c
        sage: iet.GeneralizedPermutation([[0,1,2,3,1],[4,2,5,3,5,4,0]])
        0 1 2 3 1
        4 2 5 3 5 4 0

    Creation of reduced generalized permutations::

        sage: iet.GeneralizedPermutation('a b b', 'c c a', reduced = True)
        a b b
        c c a
        sage: iet.GeneralizedPermutation('a a b b', 'c c d d', reduced = True)
        a a b b
        c c d d

    Creation of flipped generalized permutations::

        sage: iet.GeneralizedPermutation('a b c a', 'd c d b', flips = ['a','b'])
        -a -b  c -a
         d  c  d -b

    TESTS::

        sage: type(iet.GeneralizedPermutation('a b b', 'c c a', reduced=True))
        <class 'surface_dynamics.interval_exchanges.reduced.ReducedPermutationLI'>
        sage: type(iet.GeneralizedPermutation('a b b', 'c c a', reduced=False))
        <class 'surface_dynamics.interval_exchanges.labelled.LabelledPermutationLI'>
        sage: type(iet.GeneralizedPermutation('a b b', 'c c a', reduced=True, flips=['a','b']))
        <class 'surface_dynamics.interval_exchanges.reduced.FlippedReducedPermutationLI'>
        sage: type(iet.GeneralizedPermutation('a b b', 'c c a', reduced=False, flips=['a','b']))
        <class 'surface_dynamics.interval_exchanges.labelled.FlippedLabelledPermutationLI'>
    """
    if arg2 is None:
        from .template import Permutation as Permutation_class
        if isinstance(arg1, Permutation_class):
            return GeneralizedPermutation(
                arg1.list(),
                reduced=(arg1._labels is None) if reduced is None else reduced,
                flips=arg1.flips() if flips is None else flips,
                alphabet=arg1.alphabet() if alphabet is None else alphabet)

    if reduced is None:
        reduced = False

    a = _two_lists(arg1, arg2)

    l = a[0] + a[1]
    letters = set(l)

    if flips is not None:
        for letter in flips:
            if letter not in letters:
                raise ValueError("flips contains not valid letters")

    for letter in letters:
        if l.count(letter) != 2:
            raise ValueError("letters must appear twice")

    b0 = a[0][:]
    b1 = a[1][:]
    for letter in letters:
        if b0.count(letter) == 1:
            del b0[b0.index(letter)]
            del b1[b1.index(letter)]

    if not b0 and not b1:
        return Permutation(a[0], a[1], reduced=reduced, flips=flips, alphabet=alphabet)

    elif not b0 or not b1:
        raise ValueError("no admissible length")

    if reduced:
        if flips is None:
            from .reduced import ReducedPermutationLI as cls
        else:
            from .reduced import FlippedReducedPermutationLI as cls
    else:
        if flips is None:
            from .labelled import LabelledPermutationLI as cls
        else:
            from .labelled import FlippedLabelledPermutationLI as cls

    return cls(a, alphabet=alphabet, reduced=reduced, flips=flips)


def Permutations_iterator(nintervals=None,
                          irreducible=True,
                          reduced=False,
                          alphabet=None):
    r"""
    Returns an iterator over permutations.

    This iterator allows you to iterate over permutations with given
    constraints. If you want to iterate over permutations coming from a given
    stratum you have to use the module ? and
    generate Rauzy diagrams from connected components.

    INPUT:

    - ``nintervals`` - non negative integer

    - ``irreducible`` - boolean (default: True)

    - ``reduced`` - boolean (default: False)

    - ``alphabet`` - alphabet (default: None)

    OUTPUT:

    iterator -- an iterator over permutations

    EXAMPLES::

        sage: from surface_dynamics import *

    Generates all reduced permutations with given number of intervals::

        sage: P = iet.Permutations_iterator(nintervals=2,alphabet="ab",reduced=True)
        sage: for p in P: print("%s\n* *" % p)
        a b
        b a
        * *
        sage: P = iet.Permutations_iterator(nintervals=3,alphabet="abc",reduced=True)
        sage: for p in P: print("%s\n* * *" % p)
        a b c
        b c a
        * * *
        a b c
        c a b
        * * *
        a b c
        c b a
        * * *
    """
    from .labelled import LabelledPermutationsIET_iterator
    from .reduced import ReducedPermutationsIET_iterator

    if nintervals is None:
        if alphabet is None:
            raise ValueError("You must specify an alphabet or a length")
        else:
            alphabet = Alphabet(alphabet)
            if alphabet.cardinality() is Infinity:
                raise ValueError("You must specify a length with infinite alphabet")
            nintervals = alphabet.cardinality()

    elif alphabet is None:
        alphabet = range(1, nintervals + 1)

    if reduced:
        return ReducedPermutationsIET_iterator(
            nintervals,
            irreducible=irreducible,
            alphabet=alphabet)
    else:
        return LabelledPermutationsIET_iterator(
            nintervals,
            irreducible=irreducible,
            alphabet=alphabet)


@rename_keyword(
    lr_inversion='left_right_inversion',
    tb_inversion='top_bottom_inversion')
def RauzyDiagram(arg1, arg2=None, reduced=False, flips=None, alphabet=None,
        right_induction=True, left_induction=False,
        left_right_inversion=False,
        top_bottom_inversion=False,
        symmetric=False):
    r"""
    Return an object coding a Rauzy diagram.

    The Rauzy diagram is an oriented graph with labelled edges. The set of
    vertices corresponds to the permutations obtained by different operations
    (mainly the .rauzy_move() operations that corresponds to an induction of
    interval exchange transformation). The edges correspond to the action of the
    different operations considered.

    It first appeard in the original article of Rauzy [Rau80]_.

    INPUT:

    - ``intervals`` - lists, or strings, or tuples

    - ``reduced`` - boolean (default: False) to precise reduction

    - ``flips`` - list (default: []) for flipped permutations

    - ``right_induction`` - boolean (default: True) consideration of left
      induction in the diagram

    - ``left_induction`` - boolean (default: False) consideration of right
      induction in the diagram

    - ``left_right_inversion`` - boolean (default: False) consideration of
      inversion

    - ``top_bottom_inversion`` - boolean (default: False) consideration of
      reversion

    - ``symmetric`` - boolean (default: False) consideration of the symmetric
      operation

    OUTPUT:

    Rauzy diagram -- the Rauzy diagram that corresponds to your request

    EXAMPLES::

        sage: from surface_dynamics import *

    Standard Rauzy diagrams::

        sage: iet.RauzyDiagram('a b c d', 'd b c a')
        Rauzy diagram with 12 permutations
        sage: iet.RauzyDiagram('a b c d', 'd b c a', reduced = True)
        Rauzy diagram with 6 permutations

    Extended Rauzy diagrams::

        sage: iet.RauzyDiagram('a b c d', 'd b c a', symmetric=True)
        Rauzy diagram with 144 permutations

    Using Rauzy diagrams and path in Rauzy diagrams::

        sage: r = iet.RauzyDiagram('a b c', 'c b a')
        sage: r
        Rauzy diagram with 3 permutations
        sage: p = iet.Permutation('a b c','c b a')
        sage: p in r
        True
        sage: g0 = r.path(p, 'top', 'bottom','top')
        sage: g1 = r.path(p, 'bottom', 'top', 'bottom')
        sage: g0.is_loop()
        True
        sage: g1.is_loop()
        True
        sage: g0.is_full()
        False
        sage: g1.is_full()
        False
        sage: g = g0 + g1
        sage: g
        Path of length 6 in a Rauzy diagram
        sage: g.is_loop()
        True
        sage: g.is_full()
        True
        sage: m = g.matrix()
        sage: m
        [1 1 1]
        [2 4 1]
        [2 3 2]
        sage: s = g.orbit_substitution()
        sage: print(s)
        a->acbbc, b->acbbcbbc, c->acbc
        sage: s.incidence_matrix() == m
        True

    We can then create the corresponding interval exchange transformation and
    comparing the orbit of `0` to the fixed point of the orbit substitution::

        sage: v = m.eigenvectors_right()[-1][1][0]
        sage: T = iet.IntervalExchangeTransformation(p, v).normalize()
        sage: print(T)
        Interval exchange transformation of [0, 1[ with permutation
        a b c
        c b a
        sage: w1 = []
        sage: x = 0
        sage: for i in range(20):
        ....:  w1.append(T.in_which_interval(x))
        ....:  x = T(x)
        sage: w1 = Word(w1)
        sage: w1
        word: acbbcacbcacbbcbbcacb
        sage: w2 = s.fixed_point('a')
        sage: w2[:20]
        word: acbbcacbcacbbcbbcacb
        sage: w2[:20] == w1
        True
    """
    p = GeneralizedPermutation(
        arg1, arg2,
        reduced=reduced,
        flips=flips,
        alphabet=alphabet)

    return p.rauzy_diagram(
        right_induction=right_induction,
        left_induction=left_induction,
        left_right_inversion=left_right_inversion,
        top_bottom_inversion=top_bottom_inversion,
        symmetric=symmetric)

# TODO
# def GeneralizedPermutation_iterator():
#     pass


def IntervalExchangeTransformation(permutation=None, lengths=None):
    """
    Constructs an Interval exchange transformation.

    An interval exchange transformation (or iet) is a map from an
    interval to itself. It is defined on the interval except at a finite
    number of points (the singularities) and is a translation on each
    connected component of the complement of the singularities. Moreover it is a
    bijection on its image (or it is injective).

    An interval exchange transformation is encoded by two datas. A permutation
    (that corresponds to the way we echange the intervals) and a vector of
    positive reals (that corresponds to the lengths of the complement of the
    singularities).

    INPUT:

    - ``permutation`` - a permutation

    - ``lengths`` - a list or a dictionary of lengths

    OUTPUT:

    interval exchange transformation -- an map of an interval

    EXAMPLES::

        sage: from surface_dynamics import *

    Two initialization methods, the first using a iet.Permutation::

        sage: p = iet.Permutation('a b c','c b a')
        sage: t = iet.IntervalExchangeTransformation(p, {'a':1,'b':0.4523,'c':2.8})

    The second is more direct::

        sage: t = iet.IntervalExchangeTransformation(('a b','b a'),{'a':1,'b':4})

    It's also possible to initialize the lengths only with a list::

        sage: t = iet.IntervalExchangeTransformation(('a b c','c b a'),[0.123,0.4,2])

    The two fundamental operations are Rauzy move and normalization::

        sage: t = iet.IntervalExchangeTransformation(('a b c','c b a'),[0.123,0.4,2])
        sage: s = t.rauzy_move()
        sage: s_n = s.normalize(t.length())
        sage: s_n.length() == t.length()
        True

    A not too simple example of a self similar interval exchange transformation::

        sage: p = iet.Permutation('a b c d','d c b a')
        sage: d = p.rauzy_diagram()
        sage: g = d.path(p, 't', 't', 'b', 't', 'b', 'b', 't', 'b')
        sage: m = g.matrix()
        sage: v = m.eigenvectors_right()[-1][1][0]
        sage: t = iet.IntervalExchangeTransformation(p,v)
        sage: s = t.rauzy_move(iterations=8)
        sage: s.normalize() == t.normalize()
        True
    """
    from .iet import IntervalExchangeTransformation as _IET
    from .labelled import LabelledPermutationIET
    from .template import Permutation as Permutation_class

    if isinstance(permutation, Permutation_class) and permutation._flips is not None:
        raise TypeError("interval exchange with flips not yet implemented")
    elif isinstance(permutation, LabelledPermutationIET):
        p = permutation
    elif isinstance(permutation, tuple):
        p = Permutation(*permutation)
    else:
        p = Permutation(permutation)

    if len(lengths) != len(p):
        raise ValueError("bad number of lengths")

    if isinstance(lengths, dict):
        it = lengths.values()
    else:
        it = iter(lengths)
    for x in it:
        try:
            y = float(x)
        except ValueError:
            raise TypeError("unable to convert x (='%s') into a real number" % (str(x)))

        if x < 0:
            raise ValueError("lengths must be non-negative, got {}".format(y))

    return _IET(p, lengths)


IET = IntervalExchangeTransformation


def IntervalExchangeTransformationFamily(*args):
    r"""
    Return a linear family of interval exchange transformations

    INPUT: either an interval exchange transformation or a pair consisting of a
    permutation and a cone

    EXAMPLES::

        sage: from surface_dynamics import *
        sage: p = iet.Permutation([0,1,2,3,4,5],[5,4,3,2,1,0])
        sage: rays = [[5, 1, 0, 0, 3, 8], [2, 1, 0, 3, 0, 5], [1, 0, 1, 2, 0, 3], [3, 0, 1, 0, 2, 5]]
        sage: F = iet.IETFamily(p, rays)    # optional: pplpy
    """
    try:
        from .iet_family import IETFamily
    except ImportError:
        raise ValueError('flatsurf was compiled without support for iet_family. In order '
                         'to compile flatsurf with iet_family support you need '
                         'to install pplpy with the command:\n    $ sage -pip install pplpy\n'
                         'Once done, you need to reinstall flatsurf')

    if len(args) == 1:
        T = args[0]
        from .iet import IntervalExchangeTransformation
        if not isinstance(T, IntervalExchangeTransformation):
            raise ValueError('not an iet')
        from surface_dynamics.misc.linalg import deformation_cone
        from surface_dynamics.misc.ppl_utils import ppl_convert
        C = ppl_convert(deformation_cone(T.lengths()))
        return IETFamily(T.permutation(), C)

    elif len(args) == 2:
        C = args[1]
        if isinstance(C, (tuple, list)):
            from surface_dynamics.misc.ppl_utils import ppl_cone
            C = ppl_cone(C)
        else:
            from surface_dynamics.misc.ppl_utils import ppl_convert
            C = ppl_convert(C)

        return IETFamily(args[0], C)


IETFamily = IntervalExchangeTransformationFamily


def FlipSequence(*args, **kwds):
    r"""
    Build a flip sequence corresponding to a path in a Rauzy diagram.

    A flip sequence is built from an initial permutation (built from :func:`Permutation` or
    :func:`GeneralizedPermutation`) and a sequence of Rauzy inductions that could be of the
    following form:

    - a letter ``'t'`` or ``'b'`` for top right and bottom right induction
      respectively

    - a pair of letters ``'tr'``, ``'br'``, ``'tl'`` or ``'bl'`` for top right,
      bottom right, top left and bottom left induction respectively

    For all available options, see :class:`~surface_dynamics.interval_exchanges.flip_sequence.IETFlipSequence`.

    EXAMPLES::

        sage: from surface_dynamics import iet
        sage: p = iet.Permutation('a b', 'b a')
        sage: f = iet.FlipSequence(p, ['t', 'b'])
        sage: f.substitution()
        WordMorphism: a->ab, b->abb

        sage: f = iet.FlipSequence(p, ['tr', 'bl'])
        sage: f.substitution()
        WordMorphism: a->bab, b->b
    """
    from .flip_sequence import IETFlipSequence
    return IETFlipSequence(*args, **kwds)
