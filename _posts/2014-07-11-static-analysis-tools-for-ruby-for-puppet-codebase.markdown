---
published: true
title: Static analysis tools for Ruby (for Puppet Codebase)
layout: post
tags: [puppet,staticanalysis]
categories : post
---
The main idea was investigate static analysis tools for ruby, keeping in mind the following concerns.

* It should be more useful than being just a linter
* The idea is to incorporate it to the CI, and invoke it before a commit. 
* It should be configurable and extensible (And not be too opinionated)

## Investigated tools

* [Rubocop](#rubocop)
* [Diamondback Ruby](#diamondback-ruby)
* [Laser](#laser)
* [Ruby static checker](#ruby-static-checker)
* [Rufus](#rufus)
* [Cane](#cane-262)
* [Reek](#reek)
* [Flay,Flog](#flay-flog)
* [Dust](#dust)
* [Excellent](#excellent)
* [Ruby-lint](#ruby-lint-201)

## Investigated CI Hooks

* [HoundCI](#houndci)

[Recommendations](#recommendations)

## [Rubocop](https://github.com/bbatsov/rubocop)

Of the tools investigated, rubocop seems to be the most mature and featured static analysis tool available. However, it does not really do a full static analysis of ruby code as much as Diamondback Ruby or Laser attempts to do, for example, arity of methods, non termination detection, double inclusion, whether block arguments are used etc, or typing errors.

### Features
A large number of checkers are provided, which are divided into two groups

* Lint (30)
* Style (125)

The reasoning behind each checker is provided in the [ruby style guide](https://github.com/bbatsov/ruby-style-guide) maintained by the author. Of the given checkers, I found the following to be the most useful

* Lint/ConditionPosition

```
if cond()
elsif   # this should probably be else
 y = mymethod 
 z = othermethod
end
```

* Lint/ElseLayout

```
if cond()
else y = mymethod  # this should probably be elsif
 z = othermethod
end
```

* Lint/UnreachableCode

```
def mymethod(a)
  x = a
  return x + 1
  y = x + 2
end
```

* Lint/UselessComparision

```
mycollection.sort{|a,b| a <=> a} # should probably be a <=> b
```

* Lint/LiteralInterpolation

```
x = "Here is #{'Some code'}"
```

Other than these checkers that actually found existing problems, there are a few checkers that I think would be nice to enable

* Lint/EnsureReturn

```
def mymethod
   if mycond() throw MyException
ensure
  puts 'Do this'
  return nil  # silently eats the MyException
end
```

* Lint/HandleException

```
def mymethod
  myothermethod()
rescue Exception => e # eats all exceptions
end
```

* Lint/LiteralInCondition

```
if (1 + 2 > 3)  # unintentional?
end
```

* Lint/ShadowingOuterVariable

```
def mymethod(mycoll)
  x = 100
  mycoll.collect{|x| x + 2} # which x? 
end
```

* Lint/AssignmentInCondition

```
unless x = mymethod()    # should indicate intention with: unless (x = mymethod()); x.another(); end
  x.another()
end
```

* Lint/AndOr

```
if (a and b)  # restrict _and_ and _or_ to control flow :  
  dofoo
end
```
Suggested by [sharpie](https://github.com/Sharpie)

### Limitations

* Restricted to > 1.9.2
* Requires native code (parser)
* Really hard to add more complicated cops due to the way the application is structured. For example, I tried to add a cop that would warn on assignment in condition only if the variable being assigned to, already had a value. However, the callbacks are such that, the information about variable scopes are not available at the time assignment in condition is called.

## [Diamondback Ruby](http://www.cs.umd.edu/projects/PL/druby/)

Diamond back ruby is a static analysis tool written in OCaml. Of all the tools analysed, this is the most featured tool. However, this does not support all of ruby syntax, and the development seem to have stopped in 2009. While I was not able to compile the tool on my own, I experimented with the binary they provide in the project page. However, running the tool on any example larger than a few hundred lines result in a _Stack Empty_ error. Secondly, it does not understand FFI, and hence complains about OpenSSL inclusion in puppet. After removing code from puppet that caused Druby to abort, the tool spit out a very large number of warnings. Howver, due to the way I had to get it to work (removing code that Druby failed to recognize), and because it does not understand the monkey patching, all the warnings I inspected were spurious, and hence I did not get very far with it. 


## [Laser](https://github.com/michaeledgar/laser)

Laser required a bit of effort to get running. It is abandonware with the last checkin on 2011/09/11. Unfortunately while its author demonstrates its capabilities in [rubyconf 2011](https://www.youtube.com/watch?v=Uadw9fmig_k), the github version did not seem to be able to detect the same errors. I have mailed the author, but yet to receive a response. Secondly, it works only on ruby 1.9 (does not support 1.8, and does not parse 2.0)

I read the [thesis](http://www.cs.dartmouth.edu/reports/abstracts/TR2011-686/) from the author, which suggests that the biggest contribution is the static analysis of blocks, especially block arguments, arity errors, check for whether core methods like to\_s and to\_i are not overridden to return a different type. It can also detect unreachable code, unused variables, simple non termination, double inclusion etc. However, not all of ruby syntax is supported, and not all of ruby stdlib.


## [ruby static checker](https://github.com/gdb/ruby-static-checker)

Looks for typo'd variable names

## [rufus](https://github.com/jmettraux/rufus-treechecker)

Can detect excluded code patterns. Useful for security purposes, but not as a general static checker.

## [Cane](https://github.com/square/cane) 2.6.2

Cane is a style checker, primarily concerned with method complexity style, documentation and other metrics.

## [Reek](https://github.com/troessner/reek)

Reek is a codesmell detector. While useful to run once in a while, it's featureset does not seem very useful for checks

## [Flay,Flog](http://ruby.sadi.st/Ruby_Sadist.html)

From the analysis [here](http://www.infoq.com/news/2008/11/static-analysis-tool-roundup), Flay is a duplicate detector, while Flog is a complexity metrics checker.

## [Dust](https://github.com/kevinclark/dust)

Simple linter. Supports a very limited subset of rubocop.

## [Excellent](https://github.com/simplabs/excellent/wiki)

### Features

* AbcMetricMethodCheck – reports methods with an ABC metric score that is higher than the threshold.
* AssignmentInConditionalCheck – reports conditionals that test an assignment.
* CaseMissingElseCheck – reports case statements that don’t have an else clause.
* ClassLineCountCheck – reports classes which have more lines than the threshold.
* ClassNameCheck – reports classes with bad names.
* ControlCouplingCheck – reports methods that check the value of a parameter to decide which execution path to take.
* CyclomaticComplexityBlockCheck – reports blocks with a cyclomatic complexity metric score that is higher than the threshold.
* CyclomaticComplexityMethodCheck – reports methods with a cyclomatic complexity metric score that is higher than the threshold.
* EmptyRescueBodyCheck – reports empty rescue blocks.
* FlogBlockCheck – reports blocks with a Flog metric score that is higher than the threshold.
* FlogClassCheck – reports classes with a Flog metric score that is higher than the threshold.
* FlogMethodCheck – reports methods with a Flog metric score that is higher than the threshold.
* ForLoopCheck – reports code that uses for loops.
* MethodLineCountCheck – reports methods which have more lines than the threshold.
* MethodNameCheck – reports methods with bad names.
* ModuleLineCountCheck – reports modules which have more lines than the threshold.
* ModuleNameCheck – reports modules with bad names.
* NestedIteratorsCheck – reports nested iterators.
* ParameterNumberCheck – reports method and blocks that have more parameters than the threshold.
* SingletonVariableCheck – reports class variables.
* GlobalVariableCheck – reports global variables.

Notice that it is mostly linting. I ran it over a few examles, and found that it is mostly a subset of rubocop capabilities (other than the complexity metric checks).

## [Ruby-lint](https://github.com/YorickPeterse/ruby-lint) 2.0.1

According the the author of ruby-lint, it focus on problems such as undefined methods and variables, unused method arguments or variables etc.

### [Features](http://code.yorickpeterse.com/ruby-lint/latest/file.configuration.html)

1. argument_amount
2. pedantics
3. shadowing_variables
4. undefined_methods
5. undefined_variables
6. unused_variables
7. useless_equality_checks

Unfortunately, for the two ruby versions (1.9.3, 2.1.0) tried, ruby-lint exits without producing any reports.

## [HoundCI](https://houndci.com/)

### Uses rubocop 0.22 (latest rubocop is 0.24.1)

This means that a few important features (for us) are missing. It includes

* Ability to configure directories separately (Include|Exclude) (for enabling strict lib/puppet/pops )
* Or inheritance (another way to do the above) (There can be only one .hound.yml file per project)
* Configuration style is some what different between 0.22 and 0.24.1 rubocop, so we cant reuse our configuration directly on newer rubocop.


Some cops may be missing, however, the coops we are initially interested in were there

* AndOr
* ElseLayout
* ConditionPosition
* UnreachableCode
* UselessComparison

## Recommendations

My recommendation is to start with rubocop, enabling only the four cops that gave useful warnings. Since rubocop can check individual ruby files, and even a complete run of the entire code base takes only 20 seconds, it can be used as a tool during development, for validating commits. The other recommended cops may be enabled in a later commit. We should only enable further cops after ensuring that the idioms they enforce are actually useful.
