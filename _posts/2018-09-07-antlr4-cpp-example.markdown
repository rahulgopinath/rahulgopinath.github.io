---
published: true
title: Generating a parser in c++ with ANTLR4
layout: post
comments: true
tags: parsing
categories: post
---

## Using ANTLR4 for C++ target

For my research, I often need to produce recognizers of languages using different kinds of parsers.
`ANTLR4` produces _Adaptive LL(*)_ parsers ([Parr 2011](/references#parr2011ll)), and here is a bare-bones example of how to produce a `c++` implmenentation from an [ANTLR4](http://www.antlr4.org/) grammar.

First, the grammar, to be placed in a file `Expr.g4`. This is a simple expression grammar. Note that the filename is important and should match the `grammar`. Secondly, the EOF at the end of main rule is important. Otherwise the parser will not signal an error if there are unparsed characters.

```ebnf
grammar Expr;

main: expr EOF;
expr: expr ('*'|'/') expr
    | expr ('+'|'-') expr
    | INT
    | '(' expr ')'
    ;
INT     : [0-9]+ ;
```
You need to install `antlr4` or download the `antlr4` jar file to compile this grammar. `antlr4` can be installed in OSX using `brew`.
```bash
$ brew install antlr4
```
You will also need to download the corresponding runtime for your platform.
Next, we need to implement a simple driver. That is done as follows
```cpp
#include <iostream>
#include <strstream>
#include <string>
#include "antlr4-runtime.h"
#include "ExprLexer.h"
#include "ExprParser.h"

class MyParserErrorListener: public antlr4::BaseErrorListener {
  virtual void syntaxError(
      antlr4::Recognizer *recognizer,
      antlr4::Token *offendingSymbol,
      size_t line,
      size_t charPositionInLine,
      const std::string &msg,
      std::exception_ptr e) override {
    std::ostrstream s;
    s << "Line(" << line << ":" << charPositionInLine << ") Error(" << msg << ")";
    throw std::invalid_argument(s.str());
  }
};

int main(int argc, char *argv[]) {
  antlr4::ANTLRInputStream input(argv[1]);
  ExprLexer lexer(&input);
  antlr4::CommonTokenStream tokens(&lexer);

  MyParserErrorListener errorListner;

  tokens.fill();
  // Only if you want to list the tokens
  // for (auto token : tokens.getTokens()) {
  //  std::cout << token->toString() << std::endl;
  // }
  
  ExprParser parser(&tokens);
  parser.removeErrorListeners();
  parser.addErrorListener(&errorListner);
  try {
    antlr4::tree::ParseTree* tree = parser.main();
    std::cout << tree->toStringTree() << std::endl;
    return 0;
  } catch (std::invalid_argument &e) {
    std::cout << e.what() << std::endl;
    return 10;
  }
}
```
Compilation can be accomplished by using the following `Makefile`
```make
OUTPUT=output
GENERATED=generated
RUNTIME=../runtime
CCARGS=-c -I $(RUNTIME)/antlr4-runtime/ -I $(GENERATED) -std=c++11	
LDARGS=-g
LIBS=$(RUNTIME)/lib/libantlr4-runtime.a
CC=g++
GRAMMAR=Expr
ANTLR4=$(JAVA) -jar antlr-4.7-complete.jar
ANTLR4=antlr4

ANTLRGEN=BaseListener Lexer Listener Parser 
OBJS=$(addsuffix .o,$(addprefix $(OUTPUT)/$(GRAMMAR),$(ANTLRGEN)))
GSOURCES=$(addsuffix .cpp,$(addprefix $(GENERATED)/$(GRAMMAR),$(ANTLRGEN)))

.precious: $(GSOURCES)

all: parser

parser: dirs antlr4 parser.cpp $(OBJS)
	$(CC) $(CCARGS) parser.cpp  -o $(OUTPUT)/parser.o 
	$(CC) $(LDARGS) $(OUTPUT)/parser.o $(OBJS) $(LIBS) -o parser

antlr4: $(GENERATED)/.generated;
 
$(GENERATED)/.generated: $(GRAMMAR).g4
	$(ANTLR4) -Dlanguage=Cpp -o $(GENERATED) $(GRAMMAR).g4
	@touch $(GENERATED)/.generated

$(OUTPUT)/%.o : $(GENERATED)/%.cpp
	$(CC) $(CCARGS) $< -o $@

$(GENERATED)/%.cpp: $(GENERATED)/.generated;

dirs:; mkdir -p $(OUTPUT) $(GENERATED) 
clean:; rm -rf $(OUTPUT) $(GENERATED)
```
You can use it as follows
```bash
$ make
$ ./parser '1+(2*3)'
```

## Using ANTLR3 for C target

If you are looking to produce `C` rather than `C++`, ANTLR4 no longer fits the bill, and we have to use `ANTLR3`. Further, the grammar accepted by `ANTLR3` is slightly more restrictive than that accepted by `ANTLR4` (It is _LL(*)_ rather than _ALL(*)_). Here is the grammar for `ANTLR3`, with its embedded C code to accept the same language as before.
```ebnf
grammar Expr;

options
{
  language=C;
}

@members
{
 #include "antlr3defs.h"
 #include "ExprLexer.h"

 int main(int argc, char * argv[]) {

    pANTLR3_INPUT_STREAM input;
    pExprLexer  lex;
    pANTLR3_COMMON_TOKEN_STREAM tokens;
    pExprParser  parser;

    input  = antlr3StringStreamNew((pANTLR3_UINT8)argv[1], ANTLR3_ENC_8BIT, strlen(argv[1]), "_");
    lex    = ExprLexerNew(input);
    tokens = antlr3CommonTokenStreamSourceNew(ANTLR3_SIZE_HINT, TOKENSOURCE(lex));
    parser = ExprParserNew(tokens);

    parser->program(parser);

    parser->free(parser);
    tokens->free(tokens);
    lex->free(lex);
    input->close(input);

    return 0;
 }
}

program: expr EOF;
expr: term  ( (PLUS|MINUS) term)*;
term: factor ( (MULT|DIV) factor)*;
factor: INT
    | OP expr CP;
INT  : (DIGIT)+;
OP: '(';
CP: ')';
PLUS: '+';
MINUS: '-';
MULT: '*';
DIV: '/';

WHITESPACE  : ( '\t' | ' ' | '\r' | '\n'| '\u000C' )+
{
    $channel = HIDDEN;
};

fragment
DIGIT: '0'..'9';
```
As before, compiling requires the runtime. Once you have that, you can generate and compile as below:
```shell
$ java -cp $ANTLR3COMPLETEJAR org.antlr.Tool -o output Expr.g
$ gcc -o expr output/*.c -I $LIBANTLR3C/ -I $LIBANTLR3C/include $LIBANTLR3C/.libs/libantlr3c.a
```
