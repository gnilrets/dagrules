"""
Common tasks for managing this project
"""

from invoke import task


@task
def test(ctx):
    """
    Runs pytest tests for project
    """

    cmd = "pytest -s -vv --tb=short --color=yes tests"
    ctx.run(cmd)


@task(
    help={
        "check": "Only runs a check, does not reformat (default: False)",
    }
)
def lint_black(ctx, check=False):
    """
    Runs the black linter.
    """

    for path in ["dagrules", "tests", "tasks.py"]:
        check_cmd = "--check" if check else ""
        cmd = f"black --line-length=100 {check_cmd} {path}"
        ctx.run(cmd)


@task
def lint_pylint(ctx):
    """
    Runs the pylint linter.
    """

    for path in ["dagrules", "tests", "tasks.py"]:
        cmd = f"pylint {path}"
        ctx.run(cmd)


@task(
    help={
        "check": "Only runs a check, does not reformat (only relevant to black linter, default: False)",
    }
)
def lint(ctx, check=False):
    """
    Runs all linters.

    """

    lint_black(ctx, check=check)
    lint_pylint(ctx)


@task
def package(ctx):
    """
    Package distribution to upload to PyPI
    """
    ctx.run("rm -rf dist")
    ctx.run("python setup.py sdist")


@task
def package_deploy(ctx):
    """
    Deploy package to PyPI
    """
    ctx.run("twine upload dist/*")
