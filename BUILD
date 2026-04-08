genrule(
    name = "pyle_bin",
    srcs = glob(["app/**/*.py", "doc/**/*.yaml"]),
    outs = ["pyle"],
    cmd = """
        /opt/homebrew/bin/nuitka \
            --onefile \
            --include-data-dir=doc=doc \
            --onefile-tempdir-spec=/tmp/nuitka-pyle \
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
