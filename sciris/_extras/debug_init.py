"""
Sciris root module

Typically just handles imports, but also sets number of threads for Numpy if SCIRIS_NUM_THREADS is set (see :class:`sc.options <sc_settings.ScirisOptions>`).
"""

from time import time
start = time()

# Handle threadcount -- may require Sciris to be imported before Numpy; see https://stackoverflow.com/questions/17053671/how-do-you-stop-numpy-from-multithreading
import os as _os
_threads = _os.getenv('SCIRIS_NUM_THREADS', '')
if _threads: # pragma: no cover
  _os.environ.update(
      OMP_NUM_THREADS        = _threads,
      OPENBLAS_NUM_THREADS   = _threads,
      NUMEXPR_NUM_THREADS    = _threads,
      MKL_NUM_THREADS        = _threads,
      VECLIB_MAXIMUM_THREADS = _threads,
)

# Optionally allow lazy loading
_lazy = _os.getenv('SCIRIS_LAZY', False)

# Otherwise, import everything
print(f'preliminaries: {time()-start}')
if not _lazy:
    from .sc_version    import *
    print(f'sc_version: {time()-start}')
    from .sc_utils      import *
    print(f'sc_utils: {time()-start}')
    from .sc_printing   import *
    print(f'sc_printing: {time()-start}')
    from .sc_nested     import *
    print(f'sc_nested: {time()-start}')
    from .sc_odict      import *
    print(f'sc_odict: {time()-start}')
    from .sc_settings   import *
    print(f'sc_settings: {time()-start}')
    from .sc_datetime   import *
    print(f'sc_datetime: {time()-start}')
    from .sc_math       import *
    print(f'sc_math: {time()-start}')
    from .sc_dataframe  import *
    print(f'sc_dataframe: {time()-start}')
    from .sc_fileio     import *
    print(f'sc_fileio: {time()-start}')
    from .sc_versioning import *
    print(f'sc_versioning: {time()-start}')
    from .sc_profiling  import *
    print(f'sc_profiling: {time()-start}')
    from .sc_parallel   import *
    print(f'sc_parallel: {time()-start}')
    from .sc_asd        import *
    print(f'sc_asd: {time()-start}')
    from .sc_plotting   import *
    print(f'sc_plotting: {time()-start}')
    from .sc_colors     import *
    print(f'sc_colors: {time()-start}')

del _os, _lazy, _threads
