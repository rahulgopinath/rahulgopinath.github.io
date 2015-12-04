---
published: false
title: Test Generation
layout: post
tags: [testgen]
categories: [post]
---

Generally speaking, there are four different techniques for generating test data.
Random Test Data Generators, Pathwise Data Generators, Goal oriented Test Data Generators (Mahmood 2007).

The specification testing approach also includes intelligent approach.


## Functional Testing Techniques

### Intelligent

## Structural Testing Techniques

## Random Approach

## Path oriented Approach

## Goal Oriented Approach

### Assertion based
### Chaining


[@wang2009comparison] : Automation tests are poor at detecting faults
Mutant killing Manual : 40% is trivial and 70% is easy.
However, JCrasher killed 43$, TestGen killed 28%, JUB killed 24%, random killed 36%, and edge coverage 66%

[@amorim2006anempirical] :
  Eclat: random test generation: Uses daicon to infer operational model based on an existing test suite.
  Symclat: Symbolic exploration engine, executes test cases symbolically.
  Java Pathfinder model checker
  Rostra
  Symstra : symbolic execution
  DART, EGT, CUTE
  Chaining Approach, Iterative relaxation

[@ferguson1996thechaining] : Uses data dependence analysis (extension of goal oriented approach)

Types of test data generators : Pairwise test data generators, data specification generators, random test data generators


Knowledge based software test generation :
  Graph traversal based generation, Model checking tools based generation, AI Planners to generate test cases

Directed Test suite augmentation:
  - Reuses existing test cases.
  Test case generation
    - Specification based: Formal models, random selection
    - Code based
        Symbolic execution to find constraints
        Execution oriented : Dynamic execution information to search for inputs, uses function minimization to solve subgoals.
        Search based :  Genetic algorithms, Tabu search, simulated annealing
        Concolic (Dynamic symbolic) : combine concrete and symbolic execution.

InParameter Order Generator [IPOG]
Automatic Efficient Test Generator [AETG]
TConfig
Test Vector Generator

HillClimbing, Simulated Annealing, Tabu Search, Great Flood, Particle Swarm Optimization

http://stackoverflow.com/questions/4747095/test-case-generation-tools
TestFul, jAutoTest, Etoc, Randoop

Searching:
  Blind:
    jAutoTest, RandOOP
  Guided:
    Etoc, TestFul

-> TestFul: an Evolutionary Test Approach for Java
testFul: Evolutionary Search based testing.
  claims:
    jAutoTest: 81.2% stmt 75.1%branch
    RandOOP:  74.5%       64.8%
    Etoc      77.3%       66.1%
    TestFul   90.1%       85.2%
On Array Partition, Binary Heap, BST, Vending Macine, DLinkList, Disjoint Set, DSetFast, Fraction, FSM, RBTree, Sorting, Stack Array, Vector
Works better for programs without state.
Can not deal with arrays and enumerations as parameters (future)
Can only deal with type erased.


Search-based Software Test Data Generation: A Survey
-> Hill Climbing
-> Simulated Annealing
-> Evolutionary Algorithms
-> Genetic Algorithms

Test Data Generatino
-> Symbolic Execution
-> Domain Reduction (Constraint based)
-> Dynamic Structural Test data generation
    -> Random Testing
    -> Local Search
    -> Goal Oriented
    -> Chaining Approach


Evolutionary Testing of Stateful Systems: a Holistic Approach: Matteo Miraz
Non Search Based:
  Specificatino Based
  Symbolic Execution : Exponential growth of paths, cant manage large and complex programs.

Random Testing
  Auto Test: Random Testing - def use coverage of 25%
  Adaptive Random Testing
  Taboo Search
Guided Search: Coverage oriented and Structure oriented.
  Chaining: Join control flow and data flow analysis
  Evolutionary search: Memetic algorithms, Distribution Algorithms, Particle Swarm Optimations
    Royal Road: Hierarchical structure of schemas and stepping stones
                Isolated fitness regions
                Difficult - Multiple conflicting solutions
  Immune system simulation


T2 framework: random testing using specifications
  claims block coverage from 72% to 98%, branch coverage from 69 to 85

RandOOP: Raondom Testing
UnitChek: Model checking for units.
Korat: Constraint based test generation

** IMP **
Automated Test Case Generation by Cloning : Mathias Landhauber, Walter F Tichy
  - at Automation of Software Test (AST), 2012 7th International Workshop on
: Clones similar tests : which programmer indicated; future using JPlag
: Was able to clone 8% of all tests.



JCrasher
EClat
Jartege
JTest
Agitator
