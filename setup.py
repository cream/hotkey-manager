from cream.dist import setup

setup('src/manifest.xml',
    data_files = [
        ('share/cream/modules/cream/{pkg_name}', ['src/hotkey.py', 'src/manifest.xml'])
        ]
    )
