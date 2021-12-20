# DAG Rules

Inspired by [Oliver Twist](http://olivertwi.st/)


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
