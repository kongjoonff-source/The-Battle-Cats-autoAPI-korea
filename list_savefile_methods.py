import bcsfe.core
sh = bcsfe.core.SaveFile
methods = [m for m in dir(sh) if not m.startswith('_')]
print("\n".join(methods))