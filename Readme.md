# Updates:

## ((2026-04-10)) GPU Speedup and some disappointing discoveries
I have now written a GPU accelerated script to find the maximal order types for a given number of points. It is available in `gpu_read_and_plot.py`. This brought the computation from a few hours/days to a few seconds! Note that this script plots only the maximal configurations (those with the most non-empty triangles), however technically it could plot ALL configurations if we wanted to (but then we won't see the speedup since plotting would become the bottleneck).

Anyways, a disappointing discovery was made: "TwiT configuration is not maximal after all!". This discovery happened as TwiT hypothesis got gradually weakened and broke down completely at n=8:
* 6 Points: Among the 16 possible configurations for 6 points, there are 5 maximal configurations and all of them are TwiT configurations. Good so far. However, there is one TwiT configuration which is not maximal. This means that TwiT =/=> Maximality. However, Maximality ==> TwiT (so far). 
* 7 Points: Among the 135 possible configurations for 7 points, there are 21 maximal configurations. And some of these maximal configurations satisfy TwiT while most do not. This means that, Maximality =/=> TwiT. Hence, the implication of TwiT and Maximality breaks down both ways now. However, I still have some hope that there will be always be some TwiT configurations among the maximal ones. But as I move to 8 point case, that hope also breaks down.
* 8 Points: Among the 3315 possible configurations, there are 91 maximal configurations, and not a single one of them is TwiT!!
* 9 Points: Among the 151000+ possible configurations, 78 are maximal. Somehow we see a drop in maximal configs here from n=8! TwiTs do appear here.
* 10 points: Among the 14 million possible configurations, there are 2677 maximal configurations. TwiTs do appear here.

So, it seems there is no correlation between TwiT set and the maximal configuration set.

Nevertheless, an interesting observation was made: the outermost convex hull is always a triangle (atleast upto n=10 points that we plotted). 

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
