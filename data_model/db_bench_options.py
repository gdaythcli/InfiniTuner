from pydantic import BaseModel
from data_model.utils import make_field_optional
from typing import Dict, List, Union, Literal, Optional 


# @make_field_optional
# class DBBenchOptions(BaseModel):
#     cache_size: int
#     bloom_bits: int
#     use_ribbon_filter: str
#     row_cache_size: int
#     cache_numshardbits: int
#     enable_io_prio: str
#     enable_cpu_prio: str
#     # file_checksum: str
#     use_keep_filter: str

class DBBenchOptions(BaseModel):
    cache_size: Optional[int] = None
    bloom_bits: Optional[int] = None
    use_ribbon_filter: Optional[str] = None
    row_cache_size: Optional[int] = None
    cache_numshardbits: Optional[int] = None
    enable_io_prio: Optional[str] = None
    enable_cpu_prio: Optional[str] = None
    use_keep_filter: Optional[str] = None
    