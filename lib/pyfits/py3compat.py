import sys

if sys.version_info[0] >= 3:
    # Stuff to do if Python 3
    import io
    import builtins

    # Make io.FileIO available as the 'file' builtin as Go^H^HPython 2 intended
    builtins.file = io.FileIO

    # Here we monkey patch (yes, I know) numpy to fix a few numpy Python 3
    # bugs.  The only behavior that's modified is that bugs are fixed, so that
    # should be OK.

    # Fix chararrays; this is necessary in numpy 1.5.1 and below--hopefully
    # should not be necessary later.  See
    # http://projects.scipy.org/numpy/ticket/1817
    # TODO: Maybe do a version check on numpy for this?
    import numpy
    import pyfits.rec
    import pyfits.file

    _chararray = numpy.char.chararray
    class chararray(_chararray):
        def __getitem__(self, obj):
                val = numpy.ndarray.__getitem__(self, obj)
                if isinstance(val, numpy.character):
                    temp = val.rstrip()
                    if numpy.char._len(temp) == 0:
                        val = ''
                    else:
                        val = temp
                return val
    for m in [numpy.char, numpy.core.defchararray, numpy.record, pyfits.rec]:
        m.chararray = chararray

    # Fix recarrays with sub-array fields.  See
    # http://projects.scipy.org/numpy/ticket/1766
    # TODO: Same as above
    def _fix_dtype(dtype):
        """
        Numpy has a bug (in Python3 only) that causes a segfault when
        accessing the data of arrays containing nested arrays.  Specifically,
        this happens if the shape of the subarray is not given as a tuple.
        See http://projects.scipy.org/numpy/ticket/1766.
        """

        if dtype.fields is None:
            return dtype

        new_dtype = []
        for name in dtype.names:
            field = dtype.fields[name][0]
            shape = field.shape
            if not isinstance(shape, tuple):
                shape = (shape,)
            new_dtype.append((name, field.base, shape))

        return numpy.dtype(new_dtype)

    _recarray = numpy.recarray
    class recarray(_recarray):
         def __new__(subtype, shape, dtype=None, buf=None, offset=0,
                     strides=None, formats=None, names=None, titles=None,
                     byteorder=None, aligned=False, heapoffset=0, file=None):
             if dtype is not None:
                 dtype = _fix_dtype(dtype)

             return _recarray.__new__(
                     subtype, shape, dtype, buf, offset, strides, formats,
                     names, titles, byteorder, aligned, heapoffset, file)
    numpy.recarray = recarray

    # Do the same for the rec.recarray that comes with PyFITS (can this go
    # away yet?)
    _recarray = pyfits.rec.recarray
    class recarray(_recarray):
         def __new__(subtype, shape, dtype=None, buf=None, offset=0,
                     strides=None, formats=None, names=None, titles=None,
                     byteorder=None, aligned=False, heapoffset=0, file=None):
             if dtype is not None:
                 dtype = _fix_dtype(dtype)

             return _recarray.__new__(
                     subtype, shape, dtype, buf, offset, strides, formats,
                     names, titles, byteorder, aligned, heapoffset, file)
    pyfits.rec.recarray = recarray

    # We also need to patch pyfits.file._File which can also be affected by the
    # #1766 bug
    old_File = pyfits.file._File
    class _File(old_File):
        def readarray(self, size=None, offset=None, dtype=numpy.uint8,
                      shape=None):
            if isinstance(dtype, numpy.dtype):
                dtype = _fix_dtype(dtype)
            return old_File.readarray(self, size, offset, dtype, shape)
        readarray.__doc__ = old_File.readarray.__doc__
    pyfits.file._File = _File
else:
    # Stuff to do if not Python 3
    pass
