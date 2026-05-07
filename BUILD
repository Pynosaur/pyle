genrule(
    name = "pyle_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]) + [".program"],
    outs = ["pyle"],
    cmd = """
        PYLE_VER=$$(grep '^version:' $(location .program) | cut -d' ' -f2)
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --onefile-tempdir-spec=/tmp/nuitka-pyle-$$PYLE_VER \
            --no-progressbar \
            --assume-yes-for-downloads \
            --no-deployment-flag=self-execution \
            --output-dir=$$(dirname $(location pyle)) \
            --output-filename=pyle \
            $(location app/main.py)
    """,
    local = 1,
    visibility = ["//visibility:public"],
)
