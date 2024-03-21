# -----------------------------------------------------#
#                   Library imports                    #
# -----------------------------------------------------#
from pathlib import Path

import mkdocs_gen_files

# -----------------------------------------------------#
#                    Configuration                     #
# -----------------------------------------------------#
# Package source code relative path
src_dir = "sqlalchemy_bind_manager"
# Generated pages will be grouped in this nav folder
nav_pages_path = "API-Reference"


# -----------------------------------------------------#
#                       Runner                         #
# -----------------------------------------------------#
""" Generate code reference pages and navigation

    Based on the recipe of mkdocstrings:
    https://github.com/mkdocstrings/mkdocstrings
    https://github.com/mkdocstrings/mkdocstrings/issues/389#issuecomment-1100735216

    Credits:
    Timothée Mazzucotelli
    https://github.com/pawamoy
"""
# Iterate over each Python file
for path in sorted(Path(src_dir).rglob("*.py")):
    # Get path in module, documentation and absolute
    module_path = path.relative_to(src_dir).with_suffix("")
    doc_path = path.relative_to(src_dir).with_suffix(".md")
    full_doc_path = Path(nav_pages_path, doc_path)

    # Handle edge cases
    parts = (src_dir, *tuple(module_path.parts))
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    # Write docstring documentation to disk via parser
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")
    # Update parser
    mkdocs_gen_files.set_edit_path(full_doc_path, path)
