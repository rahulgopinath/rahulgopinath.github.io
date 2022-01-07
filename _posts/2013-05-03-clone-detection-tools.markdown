---
published: true
title: Clone Detection Tools
layout: post
comments: true
tags: [clones]
categories : post
---

Here is a summary of clone detection tools, state of the art.

## FOSS

Uses protein alignment matrix (the agent is called bSAM) for
matching source code. A later algorithm is called Program Alignment Matrix

Effectively it determines the percentage of symbols in A that aligns
with symbols in B and vice versa. It is somewhat similar to the *diff*
algorithm

The matching of licenses itself is a more mundane affair. It uses
a set of trigger words to determine if the source code contains a
license. If it does, then the questionable section is extracted and is
matched against a secondary list of confirmation words. If both match,
then it flags the source file as very likely to contain a license.

I looked at clone detection, plagiarism detection and origin analysis
Here is a brief summary.

Pure Text based:  (No tokenization)
----------------
- Levenstein distance,
- Kolmogrov Complexity based (compressed length) - SID
- Tokenized approach. - Dup
- Suffix tree algorithm for longest matching pairs
      line by line matching (hash per line)
- Use fingerprinting algorithm for all length *n* substrings
      Karp-Rabin algorithm
- Dynamic Pattern Matching algorithm (*Diff*)
- Use Latent semantic indexing - comments and identifier matching.
  Linguistic analysis

Token based: parsed into sequence of tokens
-----------
- CCFinder (remove uninteresting elements, normalize,
  relate each token to type/identifier/var/const)
  Use a suffix tree based substring matching to find similar subsequences (tokens)
  Use parametrized matching + above.
- CP-Miner - frequent subsequence mining (actually duplication analysis)

AST Based: Tree methods
--------------
- CloneDR - annotated parse tree comparison using characterization metrics
  based on hash function through tree matching. also does parametrized matching.
- Change to intermediate language, and then compare.
- Use structural abstraction using parametrization.

Program dependency graph : Tree methods
-------------------------
- Semantic information & isomorphic subgraph matching
- program slicing to find similar portions.
- k-length patch matching for maximal similar subgraphs.

Metrics based:
-------------
- Fingerprinting approaches with n-dim matrix vectors. Flattened to IL
- Abstract pattern matching tool using Markov models.
      (finds similarity between two programs)
  cyclomatic complexity, function point metric, information flow quality metric
- Halstead metrics (#function calls, #variables, #operators etc.)

Feature based:
--------------
- Parametrized approach with neural networks to find similar blocks.

Hybrid approaches:
----------------
- AST nodes are serialized in pre-order traversal,
  suffix trees created.
  Compares tokens of AST nodes using a suffix tree based algorithm
- Transformed AST sequence matching
  Characteristic vectors are computed to approximate structural
  info within ASTs in Euclidean space. A locality sensitive hashing is
  then used for clustering

