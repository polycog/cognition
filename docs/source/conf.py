# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Cognition'
copyright = '2026, Polycog, Inc.'
author = 'Polycog, Inc.'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'autoapi.extension', 'myst_parser']

autodoc_typehints = 'description'
autoapi_python_class_content = 'both'
autoapi_dirs = ['../../src/cognition']
autoapi_options = [
    'members',
    'undoc-members',
    # 'private-members',
    'show-inheritance',
    'show-module-summary',
    'special-members',
    # 'imported-members',
]

myst_enable_extensions = [
    "attrs_block",
    "colon_fence",
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = 'shibuya'
html_static_path = ['_static']

html_theme_options = {
}
html_favicon = "_static/favicon.ico"


# ===

# pylint: disable=missing-function-docstring
def skip_member(_app, _what, name, _obj, skip, _options): # type: ignore
    private_but_keep = (
        "cognition.decision.state.SelfReinitState._reinit",
        "cognition.decision.state.SelfElaborationState._elaborate"
    )
    if name in private_but_keep:
        return False

    return skip

# pylint: disable=missing-function-docstring
def setup(sphinx): # type: ignore
    sphinx.connect("autoapi-skip-member", skip_member)
