from ytdream.utils.validation import validate_url
from ytdream.services.queue_manager import QueueManager, QueueTask

def test_url_validation():
    assert validate_url("https://www.youtube.com/watch?v=abc")
    assert validate_url("http://example.com/video")
    assert not validate_url("javascript:alert(1)")
    assert not validate_url("not a url")

def test_queue_add_remove():
    q=QueueManager(); t=q.add(QueueTask(url="https://example.com"))
    assert q.next_pending() is t
    assert q.remove(t.id)
    assert q.next_pending() is None

def test_running_task_cannot_be_removed():
    q=QueueManager(); t=q.add(QueueTask(url="https://example.com")); t.status="Berjalan"
    assert not q.remove(t.id)
