# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../app/resources', 'resources'),
        ('../SLRinator/comprehensive_bluebook_rules.json', 'resources'),
        ('../app/gui/styles.qss', 'gui'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyMuPDF',
        'fitz',
        'google.auth',
        'google.oauth2',
        'googleapiclient',
        'openai',
        'anthropic',
        'docx',
        'cryptography',
        'keyring',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SLR Citation Processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SLR Citation Processor',
)

# For macOS .app bundle
app = BUNDLE(
    coll,
    name='SLR Citation Processor.app',
    icon=None,
    bundle_identifier='edu.stanford.law.citation-processor',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
    },
)
