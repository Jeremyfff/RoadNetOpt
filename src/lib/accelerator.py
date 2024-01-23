import clr
import os
clr.AddReference(os.path.abspath(r'lib/RoadNetOptAccelerator/bin/Debug/RoadNetOptAccelerator'))
from RoadNetOptAccelerator import CAccelerator
cAccelerator = CAccelerator()

cAccelerator.SetMaxChunks(16)
cAccelerator.SetMinGeoPerChunk(4)