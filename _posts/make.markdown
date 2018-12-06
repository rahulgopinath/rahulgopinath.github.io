### Makefiles best practices

Here is one of the best practices that we followed at Sun, that does not seem to have been documented elsewhere, but made life simpler.

The idea is to thread dependencies, with entry targets treated as leaves. For example

```
extract: project/.extracted

project/.extracted: project.tar.gz
    $(EXTRACT) project.tar.gz
    touch project/.extracted

preprocess: project/.preprocessed

project/.preprocessed: project/.extracted
    $(preprocess) proj/*.c
    touch project/.preprocessed
```

This lets you make use of shorter names for invoking in-between stages, and to ensure that you don't do more work than necessary.

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

If not, you will come to grief when some poor programmer decides to use make -j <n> or uses one of the parallel makes. Make use of the tools such as gvmake to ensure that the dependencies are correctly ordered.

Use `--debug=basic -n` to view which files need to be remade, and GNU [remake](http://bashdb.sourceforge.net/remake/) for debugging.
