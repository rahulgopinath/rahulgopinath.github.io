### Makefiles best practices


#### Automatic variables are your friends.

* `$@` is the name of the target. Make it a habit to `touch $@` at the end of the make rule for timestamps, or if it is the name of a useful target, generate `.$@` or `$@~` if `$@` includes a path, and finally `mv .$@ $@` as the last step.
* `$*` is the matched portion represented by `%` in makefile targets. Confusingly `$%` is used for another purpose.
* `$<` is the name of the first prerequisite.
* Attaching parenthesis and `D` and `F` respectively gets you file and directory parts of these variabls. For example, `$(@D)` is the directory part of the target while `$(@F)` is the file part.

#### Thread dependencies, with entry targets treated as leaves

```
extract: project/.extracted

project/.extracted: project.tar.gz
    $(EXTRACT) $<
    touch $@

preprocess: project/.preprocessed

project/.preprocessed: project/.extracted
    $(preprocess) project/*.c
    touch $@
```

This lets you make use of shorter names for invoking in-between stages, and to ensure that you don't do more work than necessary.

#### Specify the targets as makevariables which is translated to makefile pattern rules

```
extract: project-$(target)/.extracted

project-%/.extracted: project-%.tar.gz
    $(EXTRACT) $<
    touch $@

preprocess: project-$(target)/.preprocessed

project-%/.preprocessed: project-%/.extracted
    $(preprocess) project-$*/*.c
    touch $@
```

This will be invoked as

```
make preprocess target=A
```


Another best practice is to use the make sure it exists, but don't check the timestamp dependency rule for directories, and similar targets.

```
all: $(OBJS)

$(OBJS): | $(OBJDIR)

$(OBJDIR):; mkdir $(OBJDIR)
```

Here, the OBJDIR will be created if it does not exist. If you forget the |, the dependents of OBJDIR will be recreated each time a file inside OBJDIR changes. That is, ideally,

```
%.o: %.cpp .deps
    $(CXX) $(CXXFLAGS) -c -o $@ $< -MMD -MP -MF .deps/$*.d
.deps:
    mkdir .deps
# subtle: directories are listed as changed when entries are
# created, leading to spurious rebuilds.
.deps/stamp:
    mkdir .deps && touch .deps/stamp
-include .deps/*.d
```

should be

```
%.o: %.cpp | .deps
    $(CXX) $(CXXFLAGS) -c -o $@ $< -MMD -MP -MF .deps/$*.d
.deps:
    mkdir .deps
-include .deps/*.d
```

Finally, do not rely on the ordering of recipes in the make file to ensure that the targets are build in a particular order. That is, if you have

```
a:
    touch a
b:
    touch b
c:
    touch c
```

Do not assume that the targets will be built in the order a, b, c. If you want it, then explicitly tell the makefile using dependencies

```
a:
    touch a
b: a
    touch b
c: b
    touch c
```

If not, you will come to grief when some poor programmer decides to use make -j <n> or uses one of the parallel makes. Make use of the tools such as [gvmake](https://metacpan.org/pod/release/AGENT/Makefile-GraphViz-0.18/script/gvmake) to ensure that the dependencies are correctly ordered. Use `-o make.dot` to make a dotfile and inspect the dotfile directly. It has human readable syntax.

Use `--debug=basic -n` to view which files need to be remade, and GNU [remake](http://bashdb.sourceforge.net/remake/) for debugging.

#### Remove implicit rules

```
.SUFFIXES:
```

#### Disable autoremoval of intermediate files

```
.SECONDARY:
```
