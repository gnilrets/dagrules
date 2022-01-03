# dagrules

dagrules is a tool that allows you to write your own dbt dag rules and check
that your dbt project is conforming to those rules.

## Overview

While the dbt community has established some excellent guidelines for
[how to structure dbt
projects](https://discourse.getdbt.com/t/how-we-structure-our-dbt-projects/355),
those conventions are not automatically enforced.  Those
conventions are simply guidelines, and each team may decide on a
slightly different set of conventions that work best for their
particular set up.  dagrules was developed to allow you to write your
own conventions in a simple `yaml` document, and have those
conventions enforced via your CI system.

To use dagrules, all you need is a dbt project and a `dagrules.yml`
file located in the root of the dbt project (e.g.,
`dbt/dagrules.yml`).  The yaml file should look like (for a more
complete example, see [tests/dagrules.yml](test/dagrules.yml):

````yaml
---
version: '1'
rules:
  - name: The name of my rule
    subject:
       ... # How to select nodes to check that they satisfy the rules
    must:
       ... # Define the rules that must be followed
  - name: Another one of my rules
    ...
````

### Installation and running rules

dagrules can be installed using pip:

````bash
pip install dagrules
````

And then run `dagrules` with the `--check` argument from your dbt project root:

````bash
dagrules --check
````

dagrules assumes that it is being executed from the dbt project root and that there is
a `target/manifest.json` file already present (so the dbt project must be compiled
any time the dag is changed before dagrules can be run).  These defaults can
be overridden by setting the `DBT_ROOT` and `DAGRULES_YAML` environment variable to
point to other locations.

## Subjects

For every rule, a subject should be declared that defines how to
select nodes of the dbt dag to use for rule validation.  Omitting the
subject means that the rule will be applied to every dbt model.
dagrules currently supports two ways to select subjects: 1) by node
type (source, snapshot, model) and 2) by tags.  For example, the
follow subject includes all models that are tagged "staging":

````yaml
rules:
  - name: All staging models must ...
    subject:
      type: model
      tags: staging
    must:
      ...
````


## Tag selection

Tag selection applies both to `subject` and `must` section of the
dagrules yaml spec.  Tags can be defined several ways.

**Single string** - Selecting with a single tag can be expressed as a simple string

````yaml
tags: staging
````

**List of tags: match any** - A list of tags can also be specified, and
dagrules will match nodes with **any** of the tags in the list.  The
example below will match nodes having either `base` or `intermediate`
tags.

````yaml
tags:
  - base
  - intermediate
````

**Include: match all with exclusions** - When you need to select nodes
that match **all** tags in a list, and possibly exclude nodes with
some tags as well, you can use include/exclude.  The example below
will select any nodes that have both "staging" and "finance" tags, but
that don't also have the `base` tag.

````yaml
tags:
  include:
    - staging
    - finance
  exclude:
    - base
````

The arguments to `include` and `exclude` can either be a list or single strings.


**Combine any/all** - We can also combine **any** and **all** syntaxes
at once.  The following will select all nodes that are either
"non-base staging", "core", or "mart" models.:

````yaml
tags:
  - include: staging
    exclude: base
  - core
  - mart
````

## Musts

"Musts" define the rules that must be adhered to by the subjects defined in the `subject`
section.  Multiple "musts" may be included in a rule definition, and all must be
satisfied for the rule to pass.

**Match name** - The `match-name` rule requires that each subject adhere to a
particular naming pattern.  dagrules currently only supports regular expression matching.
For example, the following rule enforces that all snapshot models must be named with
a `snap_` prefix:

````yaml
rules:
  - name: Snapshot must be prefixed with snap_
    subject:
      type: snapshot
    must:
      match-name: /snap_.*/
````

**Have tags** - The `have-tags-any` rule requires that all selected models must have
one of any of the listed tags.  The following example specifies that all nodes in the dag
must have at least one of the tags listed:

````yaml
rules:
  - name: All models must be tagged either snapshot, base, staging, intermediate, core, mart
    # Omit subject to include all nodes
    must:
      have-tags-any:
        - snaphost
        - base
        - staging
        - intermediate
        - core
        - mart
````

**Have parent or child relationship** - The `have-child-relationship`
and `have-parent-relationship` rules require that the subjects have a
certain kind of relationship to either their **immediate** children or
parents.  The types of relationship can involve:
  * `cardinality` - The cardinality of the relationship between a subject and its child/parent
    can either be `one_to_one` or `one_to_many` (default).  If `one_to_one` is selected,
    that a subject may only have one child/parent.
  * `required` - Indicates whether a child/parent relationship is required or not.  The default
    is `True`, meaning that if a relationship is defined, all subject must have at least
    one child or parent node.  If `False`, then a subject may have 0 children/parents.
  * `require-tags-any` - Contains a list of tags that the parent/child
    must have (with syntax defined in the "Tag selection" section
    above).
  * `require-node-type` - Indicates the node type (source, snapshot, model) that the child/parent
    must be in order to pass.
  * `select-tags-any` - Contains a list of tags that restricts the selection of parents/children
    involved in the rule.
  * `select-node-type` - Indicates that only the parents/children with the specified node
    type are to be considered when checking the rule.

For example,

````yaml
rules:
  - name: Snapshots must have 0 or 1 children, which must all be base models
    subject:
      type: snapshot
    must:
      have-child-relationship:
        cardinality: one_to_one
        required: false
        require-tags-any:
          - base

  - name: Intermediate models may only depend on non-base staging, core, mart, or other intermediate models
    subject:
      tags:
        include: intermediate
    must:
      have-parent-relationship:
        require-tags-any:
          - include: staging
            exclude: base
          - core
          - mart
          - intermediate
````


## Contributing

We welcome contributors!  Please submit any suggests or pull requests in Github.

### Developer setup

Create an appropriate python environment.  I like [miniconda](https://conda.io/miniconda.html),
but use whatever you like:

    conda create --name dagrules python=3.9
    conda activate dagrules

Then install pip packages

    pip install pip-tools
    pip install --ignore-installed -r requirements.txt

run tests via

    inv test

and the linter via

    inv lint
