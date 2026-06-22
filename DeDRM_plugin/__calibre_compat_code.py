
#@@CALIBRE_COMPAT_CODE_START@@
import sys, os

# Explicitly allow importing everything ...
if os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if "calibre" in sys.modules:
    # Explicitly set the package identifier so we are allowed to import stuff ...
    __package__ = "calibre_plugins.dedrm"

#@@CALIBRE_COMPAT_CODE_END@@
