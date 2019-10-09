project = "SQLAlechemy Declarative Extensions"
copyright = "2022, Dan Cardin"
author = "Dan Cardin"
release = "0.1.0"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "autoapi.extension",
]

templates_path = ["_templates"]

exclude_patterns = []

html_theme = "furo"
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

autoapi_type = "python"
autoapi_dirs = ["../../src/sqlalchemy_declarative_extensions"]
autoapi_generate_api_docs = False

autodoc_typehints = "description"
