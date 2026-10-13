from concurrent.futures import ThreadPoolExecutor
from app import db

def test_request_connection_can_move_between_worker_threads(tmp_path):
    """A sync FastAPI dependency and route may run in different worker threads."""
    c=db.connect(tmp_path/'workers.db')
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            result=pool.submit(lambda:c.execute('SELECT 1').fetchone()[0]).result()
        assert result==1
    finally:c.close()

def test_parallel_authenticated_reads(actors):
    client=actors['analyst']
    paths=['/projects/1/documents','/projects/1/members','/projects/1/requirements','/projects/1/dashboard']*4
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda path:client.get(path).status_code,paths))
    assert results==[200]*len(paths)
