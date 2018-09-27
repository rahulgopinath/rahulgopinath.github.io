---
published: false
title: Patterns in Mutants
layout: post
comments: true
tags: mutation
---

The cargo file

```ini
[package]
name = "mutants"
version = "0.1.0"
authors = ["Rahul Gopinath <rahul@gopinath.org>"]

[[bin]]
name = "mutants"
path = "src/mutants.rs"

[dependencies]
num-bigint = "0.1"
rand = "0.3"
num-traits = "0.1.41"
getopts = "0.2"
bit-vec = "0.4.4"
```

```rust
extern crate getopts;
extern crate bit_vec;
extern crate num_bigint;
extern crate num_traits;
extern crate rand;

use getopts::Options;
use rand::Rng;
use rand::distributions::{IndependentSample, Range};
use num_traits::{FromPrimitive, One, Zero};
use num_bigint::BigUint;

use std::process;
use std::env;
use std::fmt;
use std::fs;
use std::fs::File;
use std::io::Write;
use std::iter::repeat;

use std::collections::HashMap;
use bit_vec::BitVec;

#[derive(Debug)]
struct MyOptions {
    programlen: u64,
    nmutants: u64,
    ntests: u64,
    nfaults: u64,
    nchecks: u64,
    nequivalents: u64,
    subtle: u64,
}

impl fmt::Display for MyOptions {
	fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
		write!(f, "data/nfaults={:?}_ntests={:?}_nchecks={:?}_",
                  self.nfaults, self.ntests, self.nchecks)
	}
}

fn genbits(bitlen: u64, nflipped: u64) -> BigUint {
    let mut rng = rand::thread_rng();

    let faulty_bits: u64 = rng.gen_range(1, nflipped + 1);
    let rr = Range::new(0, bitlen as usize);

    (0..faulty_bits).fold(BigUint::zero(), |m, _|{
        let pos = rr.ind_sample(&mut rng);
        let fault = BigUint::one() << pos;
        m | fault
    })
}

fn gen_lst(num: u64, len: u64, nflipped: u64) -> Vec<BigUint> {
    (0..num).map(|_| genbits(len, nflipped)).collect()
}

fn gen_mutants(nmutants: u64, programlen: u64, nfaults: u64) -> Vec<BigUint> {
    gen_lst(nmutants, programlen, nfaults)
}

fn gen_tests(ntests: u64, programlen: u64, nchecks: u64) -> Vec<BigUint> {
    gen_lst(ntests, programlen, nchecks)
}

#[allow(dead_code)]
fn bitlog(bignum: &BigUint) -> () {
    eprintln!("num:{} bits: {} size: {}", bignum,  bignum.to_str_radix(2), bignum.bits());
}

fn hamming_wt(bignum: &BigUint) -> usize {
	BitVec::from_bytes(&bignum.to_bytes_be()).iter().filter(|b| *b).count()
}

fn kills(test: &BigUint, mutant: &BigUint, subtle: &usize) -> bool {
    //! If subtle == 0, we interpret the bits flipped as conditions to
    //! be satisfied. That is, all bits need to be anded.
    //! If subtle == 1, then it is same as checking if any of the bits
    //! in a mutant is detected.
    //! If subtle > 1, then it is same as adding a little bit of stubbornness
    //! to each mutant in that some of the bits are interpreted as conditions
    if *subtle == 0 {
        &(test & mutant) == mutant
    } else {
        hamming_wt(&(test & mutant)) >= *subtle
    }
}

fn zeros(size: usize) -> Vec<BigUint> {
    repeat(BigUint::zero()).take(size).collect()
}

fn ntests_mutant_killed_by(m: &BigUint, tests: &[BigUint], subtle: &usize) -> usize {
    tests.iter().filter(|t| kills(t, m, subtle)).count()
}

fn mutant_killedby_ntests(
    opts: &MyOptions,
    mutants: &[BigUint],
    equivalents: &[BigUint],
    my_tests: &[BigUint],
) -> HashMap<usize, usize> {
    mutants.iter().chain(equivalents)
        .map(|m| ntests_mutant_killed_by(m, my_tests, &FromPrimitive::from_u64(opts.subtle).unwrap()))
        .enumerate().collect()
}

fn save_csv(opts: &MyOptions, mutant_kills: &HashMap<usize, usize>) {
    let max_tests_a_mutant_killed_by = mutant_kills.iter().map(|(_m, k)| k).max().unwrap();

    let mname = format!("{}mutants.csv", opts.to_string());
    let mut f = File::create(&mname).unwrap_or_else(|e| {
      panic!("Unable to create file {}: {}", &mname, e);
    });

    writeln!(f, "mutant,killedbynt\n").expect("Unable to write data");
    for (m, killedby_n) in mutant_kills.iter() {
        writeln!(f, "{},{}\n", m, killedby_n).expect("Unable to write data");
    }

	let ntests = (0..*max_tests_a_mutant_killed_by + 1).map(|nkillingt| {
		let mut exactlynt = 0;
		let mut atmostnt = 0;
		let mut atleastnt = 0;
		for killedby_n in mutant_kills.values() {
			if *killedby_n == nkillingt {
				exactlynt += 1;
			}
			if *killedby_n >= nkillingt {
				atleastnt += 1;
			}
			if *killedby_n <= nkillingt {
				atmostnt += 1;
			}
		}
		(nkillingt, atleastnt, atmostnt, exactlynt)
	});

    let fname = format!("{}kills.csv", opts.to_string());
    let mut f = File::create(&fname).unwrap_or_else(|e| {
      panic!("Unable to create file {}: {}", &fname, e);
    });

    writeln!(f, "ntests,atleast,atmost,exactly\n").expect("Unable to write data");
    for (i, a, s, e) in ntests {
        writeln!(f, "{},{},{},{}\n", i, a, s, e).expect("Unable to write data");
    }
}

fn print_usage(program: &str, opts: &Options) {
    let brief = format!("Usage: {} [options]", program);
    print!("{}", opts.usage(&brief));
}

fn parse_arguments() -> MyOptions {
    let args: Vec<_> = env::args().collect();
    let program = &args[0];
    let mut opts = Options::new();
    opts.optflag("h", "help", "print help");
    opts.optopt("l", "programlen", "length of a mutant", "programlen");
    opts.optopt("m", "nmutants", "number of mutants", "nmutants");
    opts.optopt("t", "ntests", "number of tests", "ntests");
    opts.optopt("f", "nfaults", "maximum number of faults per mutant", "nfaults");
    opts.optopt("c", "nchecks", "maximum number of checks per test", "nchecks");
    opts.optopt("e", "nequivalents", "number of equivalents", "nequivalents");
    opts.optopt("s", "subtle", "subtlety of mutants (how many conditions need to\
		be fulfilled?) -- 0 for conditions, 1 for *any* and >1 for hamming weight", "subtle");

    let matches = match opts.parse(&args[1..]) {
        Ok(m) => m,
        Err(f) => panic!(f.to_string()),
    };

    if matches.opt_present("h") || args.len() < 2 {
        print_usage(program, &opts);
        process::exit(0);
    };

    let numeric_arg = |name, def| matches.opt_str(name).map_or(def, |s| s.parse().unwrap());

    MyOptions {
        nmutants: numeric_arg("m", 10_1000),
        programlen: numeric_arg("l", 10_1000),
        ntests: numeric_arg("t", 10_1000),
        nfaults: numeric_arg("f", 10),
        nchecks: numeric_arg("c", 10),
        nequivalents: numeric_arg("c", 0),
        subtle: numeric_arg("s", 1),
    }
}

fn main() {
    let opts = parse_arguments();
    eprintln!("{:?}", opts);

    fs::create_dir_all("./data/").unwrap_or_else(|why| {
        panic!("! {:?}", why.kind());
    });

    // first generate our tests
    let my_tests = gen_tests(opts.ntests, opts.programlen, opts.nchecks);
    // Now generate n mutants
    let mutants = gen_mutants(opts.nmutants, opts.programlen, opts.nfaults);

    let equivalents = zeros(opts.nequivalents as usize);

    // how many tests killed this mutant?
    let mutant_kills = mutant_killedby_ntests(&opts, &mutants, &equivalents, &my_tests);

    save_csv(&opts, &mutant_kills);
}
```

## Mutation Analysis Simulation

```
$ ./target/release/mutants \
           --nmutants=$nmutants \
           --programlen=$programlen \
           --nfaults=$nfaults \
           --ntests=$ntests \
           --nchecks=$nchecks
```

## Options

* nmutants : The number of mutants to be generated
* programlen : The size of the original program (number of bits)
* nfaults : The number of faults to be introduced into the mutant (it is *upto* $nfaults per mutant -- minimum of 1).
* ntests : The number of tests to be generated.
* nchecks : The number of bits checked per test (it is *upto* $nchecks per mutant -- minimum of 1)

## Description

The original program is a string of bits all set to zero, and any mutant as a
variant of that string of bits with some bits flipped. That is, `*nfaults* = number of bits set to 1`
A test is also a string of bits with a few bits set to 1. That is, `*nchecks* = number bits that are 1`.
A test kills a mutant if `(test & mutant) != 0`.

## Syntactic neighborhood (The competent programmer hypothesis)

This is controlled by `--nfaults` which produces *upto* `$nfaults` differences. If the lexical distance is to be just a single fault, then `set $nfaults=1`.

## The coupling-effect

Any test detecting a mutant will also detect any `OR` combination of mutants.

In a real system, there are always mutants that are harder to detect than simple lexical faults. These may be simulated by making (some of) the bits set in a mutant the conditions *necessary* to detect it. That is, test kills a mutant if all conditions are satisfied instead of just one. That is, `(test & mutant) == mutant`. Another implementation may be `hamming-weight(test & mutant) >= $stubbornness` where $stubbornness is set separately.

## Coverage

A test can be said to cover a given range between its most significant bit set, and the least significant bit set. A program is completely covered if all its bits are covered by the test suite.
