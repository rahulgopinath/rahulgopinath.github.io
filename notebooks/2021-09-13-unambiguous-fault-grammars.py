# ---
# published: false
# title: Unambiguous Fault Inducing Grammars
# layout: post
# comments: true
# tags: python
# categories: post
# ---

# 
# This post is the implementation of my paper [*Input Algebras*](https://rahul.gopinath.org/publications/#gopinath2021input)
# 
# In my previous post on [inducing faults](/post/2021/09/09/fault-inducing-grammar/)
# I explained the deficiency of abstract failure inducing inputs mined using
# DDSet, and showed how to overcome that by inserting that abstract (evocative)
# pattern into a grammar, producing evocative grammars that guarantee that the
# evocative fragment is present in any input generated. In this post, I will show
# how to do the opposite. That is, how to generate grammars that guarantee that
# evocative fragments are not present.
#
# As before, let us start with importing our required modules.

#^
# sympy

#@
# https://rahul.gopinath.org/py/earleyparser-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/hdd-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/simplefuzzer-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/ddset-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gatleastsinglefault-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gmultiplefaults-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gfaultexpressions-0.0.1-py2.py3-none-any.whl
# https://rahul.gopinath.org/py/gnegatedfaults-0.0.1-py2.py3-none-any.whl

# The imported modules

import hdd
import simplefuzzer as fuzzer
import gatleastsinglefault as gatleast
import gmultiplefaults as gmultiple
import gnegatedfaults as gnegated
import gfaultexpressions as gexpr

import sympy
import itertools as I

# 

class ReconstructRules(gexpr.ReconstructRules):
    def reconstruct_neg_bexpr(self, key, bexpr):
        # should never come to this because sympy simplifies.
        assert False

# 
class ReconstructRules(ReconstructRules):
    # DONE
    def or_definitions(self, rulesA, rulesB):
        AorB_rules = []
        rulesetsA, rulesetsB = [gmultiple.get_rulesets(rs)
                for rs in [rulesA, rulesB]]
        keys = set(rulesetsA.keys()) | set(rulesetsB.keys())
        for k in keys:
            new_rules = self.or_ruleset(rulesetsA.get(k, []), rulesetsB.get(k, []))
            AorB_rules.extend(new_rules)
        return AorB_rules

    # DONE
    # Each ruleset contains only rules from base rule
    def or_ruleset(self, rulesetA, rulesetB):
        # First, let us split these into common and uncommon parts.
        # this is not completely necessary, but reduces computation.
        rulesB = [r for r in rulesetB if r not in rulesetA]
        rulesA = [r for r in rulesetA if r not in rulesetB]
        new_rules = [r for r in rulesetA if r in rulesetB and r in rulesetA]

        # Now, we want to produce or(ruleA) and or(ruleB). We then minus the
        # or(ruleB) from each rule in ruleA, and minus or(ruleA) from each rule
        # in ruleB. These give us the uncommon parts (1.a and 1.b).
        # Finally, we need pairwise ands each of which becomes another rule.
        # Hint: we only need pair-wise because rulesetA and rulesetB contain
        # independent rules. Hence, 3-tuples or higher can't form.

        new_rulesA = self.from_ruleset_negate_ruleset(rulesA, rulesB)
        new_rules.extend(new_rulesA)

        new_rulesB =  self.from_ruleset_negate_ruleset(rulesB, rulesA)
        new_rules.extend(new_rulesB)

        # Next we need pair wise combinations of each rule in rulesA and rulesB
        pair_rules = []
        for rA in rulesA:
            for rB in rulesB:
                r = self.and_rules(rA, rB)
                pair_rules.append(r)
        return new_rules

    # DONE
    def from_ruleset_negate_ruleset(self, rulesA, rulesB):
        new_rulesA = []
        for r in rulesA:
            # r_ = r - or_ruleB
            r_ = self.from_rule_negate_rulelist(r, rulesB)
            new_rulesA.append(r_)
        return new_rulesA

    # DONE
    # we start with the assumption that rulesetA and rulesetB are
    # both unambiguous. If so, to remove ambiguity, given two rules
    # A1 A2 A3 on one side, and A4 A5 on the other, the result would
    # be
    # (A1 - A4|A5) or (A2 - A4|A5) or (A3 - A4|A5)    (1.a)
    # or
    # (A4 - A1|A2|A3) or (A5 - A1|A2|A3)              (1.b)
    # or (duplicated parts)
    #    (A1&A4 or A1&A5)
    # or (A2&A4 or A2&A5)
    # or (A3&A4 or A3&A5)

    def from_rule_negate_rulelist(self, rule, rulelst):
        new_rule = rule
        for r in rulelst:
            n_rs = self.unambiguous_negate_rule(r) # produces more rules.
            for nr in n_rs:
                new_rule = self.and_rule(new_rule, nr)
        return new_rule

    # TODO
    # returns a list of rules which are again unambiguous
    # The idea here is simply to generate a set of rules that do not match
    # the rule we passed in. Since this is the idea, we do not have to consider
    # the complexities of the nonterminal negation that this rule corresponds to.
    def unambiguous_negate_rule(self, rule):
        new_rules = []
        for i in range(len(rule)):
            new_rule = []
            modified = False
            for j,token in enumerate(rule):
                if i == j:
                    if not fuzzer.is_nonterminal(token):
                        modified = False
                        break
                    elif gatleast.is_base_key(token):
                        modified = False
                        break
                    else:
                        modified = True
                        new_rule.append(gnegated.negate_nonterminal(token))
                else:
                    new_rule.append(token)
            if modified:
                new_rules.append(new_rule)
        return new_rules


# Usage

my_bexpr = gexpr.BExpr('or(D1,Z1)')
grammar ={**gmultiple.EXPR_DZERO_G, **gmultiple.EXPR_DPAREN_G, **hdd.EXPR_GRAMMAR}
rr = ReconstructRules(grammar)
d1, s1 = rr.reconstruct_rules_from_bexpr('<start>', my_bexpr)
grammar[s1] = d1
remaining = gexpr.undefined_keys(grammar)
print(d1,s1)
print("remaining:", remaining)
rr = ReconstructRules({**grammar, **{s1:d1}})
d2, s2  = rr.reconstruct_rules_from_bexpr(remaining[0], my_bexpr)
grammar[s2] = d2
remaining = gexpr.undefined_keys(grammar)
print(d2,s2)
print("remaining:", remaining)

