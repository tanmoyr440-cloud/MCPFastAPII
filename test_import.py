try:
    from langchain_core.globals import set_llm_cache
    print("langchain_core.globals.set_llm_cache found")
except ImportError:
    print("langchain_core.globals.set_llm_cache NOT found")

try:
    from langchain_community.cache import SQLiteCache
    print("langchain_community.cache.SQLiteCache found")
except ImportError:
    print("langchain_community.cache.SQLiteCache NOT found")
