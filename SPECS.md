# Kode Specification

Kode is a simple programming language written mostly in natural language. This document defines the terminology for concepts and the language itself. 

## Classification

Kode is a declarative programming langauge. The langue is dynamically typed.

## Token

A token is a segment of text/numbers that is delimited by whitespace or punctuations. The following sections will further categorize tokens.

### Literal

A literal is a numerical or textual value. This can be for example `12` or `"Hello"`. (TODO: This could be further expanded if we want arrays or other primitive data-structures).

### Reserved Words

A reserved word is a word that is used for language structuring. This includes `IF`, `SET`, `PLUS`, etc. A complete list of reserved word can be found in code.

### Identifier

An identifier is label that can be assigned a value. This can be any non-reserved word following the naming convention `[a-zA-Z_][a-zA-Z0-9_]*`. By default, all identifiers are not set to any value. Using an unset identifier will lead to a compiler/runtime failure.

### Punctuation

A punctuation is a single character that delimits tokens and/or statements. This includes `.` and `,`. A complete list of reserved word can be found in code. (TODO: Not certain we will need punctuation).

## Statement

A statement is a collection of tokens that performs a certain logic. The following sections will further categorize statements.

### Operation

An operation performs logic over literals and identifiers.

#### Single Operation

```kode
1 PLUS 2
```

#### Chain Operation

```kode
X PLUS Y TIMES 12
```

#### Multiple Operation

```kode
X PLUS Y
Y PLUS X
```

### Assignment

An assignment sets the value of an identifier to a statement.  

#### Token Assignment

```kode
SET X TO 12
```

#### Statement Assignment

```kode
SET X TO 12 PLUS 2 TIMES 3
```

### Conditional

A conditional statement performs statements according to conditions. This language only supports `IF` statements (TODO: Maybe have other statements?).

#### Single Line Conditional

```kode
IF X IS EQUAL TO 2 THEN SET Y TO 1 ELSE SET Y TO 2
```

#### Clean Conditional

```kode
IF X IS GREATER THAN 12 THEN 
    SET Y TO 1 
ELSE IF X IS LESS THAN 2 THEN 
    SET Y TO 2 
ELSE 
    SET Y TO 3
```

#### Nested Conditional

```kode
IF X IS GREATER THAN 1 THEN
    IF X IS EQUAL TO 2 THEN
        SET Y TO 1
    ELSE IF X IS EQUAL TO 3 THEN
        SET Y TO 2
        SET X TO 4
    END
ELSE
    SET Y TO 3
```

### Loop

A loop statement performs statements on repeat until a condition is met. This language only supports `WHILE` statements (TODO: Maybe have other statements?).

### Single Line Loop

```kode
WHILE X IS LESS THAN 5 DO SET X TO X PLUS 1
```

### Clean Loop

```kode
WHILE Y IS NOT EQUAL TO 3 DO
    SET Y TO Y PLUS 2
```

### Nested Loop

```kode
WHILE X IS LESS THAN 3 DO
    WHILE Y IS LESS THAN 4 DO
        SET Y TO Y PLUS 1
    END
    SET X TO X PLUS 1
```
