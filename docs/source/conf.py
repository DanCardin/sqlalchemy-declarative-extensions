project = "SQLAlechemy Declarative Extensions"
copyright = "2022, Dan Cardin"
author = "Dan Cardin"
release = "0.1.0"

extensions = [
    "autoapi.extension",
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
]

templates_path = ["_templates"]

exclude_patterns = []

html_theme = "furo"
html_theme_options = {
    "navigation_with_keys": True,
}
html_static_path = ["_static"]

myst_heading_anchors = 3
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

autoapi_type = "python"
autoapi_dirs = ["../../src/sqlalchemy_declarative_extensions"]
autoapi_generate_api_docs = False

autodoc_typehints = "description"
