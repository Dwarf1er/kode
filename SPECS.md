# Kode Specification

Kode is a simple programming language written mostly in natural language. This document defines the terminology for concepts and the language itself. 

## Classification

Kode is a declarative programming langauge. The langue is dynamically typed.

## Token

A token is a segment of text/numbers that is delimited by whitespace or punctuations. The following sections will further categorize tokens.

### Literal

A literal is a concrete value. They serve as a basis of most statements and operations.

#### String

A string is delimited with either a `'` or a `"`. Unlike language like Java, these symbols and be freely interchanged.

```
"Hello World"
'Hello World'
```

#### Number

A number can be an integer or a float. A distinction is made by the interpreter while running operations.

```
1.0
1
```

#### Boolean

A boolean can be active or inactive. This is used as input and is an output to logical operations.

```
True
False
```

#### Null

A null represents the absence of a value.

```
None
```

### Reserved Word

A reserved word is a word that is used for language structuring. This includes `IF`, `SET`, `PLUS`, etc. A complet can be found [here](https://github.com/Dwarf1er/kode/blob/master/kode/tokens.py#L153).

### Operator

An operator is a reserved word used for mathematical operations. This includes `ADD`, `MINUS`, `SHL`, etc. A complese list can be found [here](https://github.com/Dwarf1er/kode/blob/master/kode/tokens.py#L187).

### Identifier

An identifier is label that can be assigned a value. This can be any non-reserved word following the naming convention `[a-zA-Z]*`. By default, all identifiers are not set to any value. Using an unset identifier will lead to a compiler/runtime failure.

### Punctuation

A punctuation is a single character that delimits tokens and/or statements. This includes `.` and `-`. A complete list of reserved word can be found [here](https://github.com/Dwarf1er/kode/blob/master/kode/tokens.py#L269).

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

#### Literal Assignment

```kode
SET X TO 12.
```

#### Statement Assignment

```kode
SET X TO 12 PLUS 2 TIMES 3.
```

### Conditional

A conditional statement performs statements according to conditions. This language only supports `IF` statements.

#### Single Line Conditional

```kode
IF X EQUALS 2 THEN SET Y TO 1. ELSE SET Y TO 2. END
```

#### Clean Conditional

```kode
IF X GREATER THAN 12 THEN 
    SET Y TO 1.
ELSE 
    IF X LESS THAN 2 THEN 
        SET Y TO 2. 
    ELSE 
        SET Y TO 3.
    END
END
```

#### Nested Conditional

```kode
IF X GREATER THAN 1 THEN
    IF X EQUALS 2 THEN
        SET Y TO 1.
    ELSE 
        IF X EQUALS 3 THEN
            SET Y TO 2.
            SET X TO 4.
        END
    END
ELSE
    SET Y TO 3.
END
```

### Loop

A loop statement performs statements on repeat until a condition is met. This language only supports `WHILE` statements.

### Single Line Loop

```kode
WHILE X IS LESS THAN 5 DO SET X TO X PLUS 1. END
```

### Clean Loop

```kode
WHILE Y LESS THAN 3 DO
    SET Y TO Y PLUS 2.
END
```

### Nested Loop

```kode
WHILE X IS LESS THAN 3 DO
    WHILE Y IS LESS THAN 4 DO
        SET Y TO Y PLUS 1.
    END

    SET X TO X PLUS 1.
END
```

### I/O

An I/O operation provides feedback/interactions to/from the user. The language supports basic input and output operations.

#### Input

```
SET X TO INPUT.
```

#### Output

```
SHOW 1.
```
