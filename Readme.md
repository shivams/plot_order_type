# ((2026-01-29)) About this Repo

In this repo, I am storing stuff related to plotting the order types for different point sizes using the order type database of Aichholzer [1, 2, 3], which is available online at: http://www.ist.tugraz.at/staff/aichholzer/research/rp/triangulations/ordertypes/

There are some important and interesting steps ahead:
1. Automatically constructing the Forward Construction Tree of Order Types (FCTOT)
2. Proving the Local->Global Maximality Preservation (LGMP) Conjecture
3. If LGMP is found to be true, then we can (hopefully) drastically reduce the complexity of the tree of order types, since we then only have to explore the maximal nodes in each step. Hence, our exploration will then be on some specific paths in that tree.
    * Can we quantify the complexity reduction here?

# Some Definitions and Explanations

## Forward Construction Tree of Order Types (FCTOT)

As we proceed from "n" to "n+1" in our forward construction of point order types, we can see that a given order type of "n", say $C_n^i$ will lead give rise to a subset of order types in "n+1". Hence, we can get directed edges from configurations in "n" to configurations in "n+1". When we add these directed edges to among these configuration nodes, what we get is a proper tree which we call FCTOT.

Here is a sample manually constructed FCTOT for n=3 to n=6:

TODO: Add image here later when I have manually constructed the FCTOT.

### Automating FCTOT Construction

Can we automate the construction of FCTOT? That is, say we have been given the order type database (from [1]), then can we fill in the directed edges to get FCTOT?

## The Local->Global Maximality Preservation (LGMP) Conjecture

If we are in a maximal region and go a step up (or down) in forward construction to a region that is locally maximal, will it also be globally maximal for that point size (n+1 or n-1).
We think that this might be true, and if it turns out to be true, it would be vastly beneficial for us, since it can drastically reduce the complexity of the tree of order types, since we then only have to explore the maximal nodes in each step. Hence, our exploration will then be on some specific paths in that tree.

# Repo Contents

Currently this repo has following files:
* `read_and_plot.py`: this reads order type files (with `.b08`, `.b16` extensions), and plots the configurations and saves them as png files in subdirectories
* `otypesXX.bYY`: order type files downloaded from Aichholzer database
* `plots_otypesXX`: subdirectories containing plot images, plotted by `read_and_plot.py`



# References


[1] O. Aichholzer and F. Aurenhammer and H. Krasser
    Enumerating Order Types for Small Point Sets with Applications
    In Proc. 17th Ann. ACM Symp. Computational Geometry, Medford,
    SoCG 2001, pages 11-18, Massachusetts, USA, 2001.

[2] O. Aichholzer and H. Krasser
    The Point Set Order Type Data Base: A Collection
    of Applications and Results
    In Proc. 13th Annual Canadian Conference on Computational Geometry
    CCCG 2001, pages 17-20, Waterloo, Ontario, Canada, 2001.

[3] O. Aichholzer and H. Krasser
    Abstract order type extension and new results on the
    rectilinear crossing number.
    Computational Geometry: Theory and Applications, 36(1):2-15, 2006.
