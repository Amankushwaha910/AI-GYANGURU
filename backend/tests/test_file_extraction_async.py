import asyncio
import struct
import threading
import time

import pytest

from app.services import file_service


@pytest.mark.asyncio
async def test_pdf_and_docx_parsers_run_off_event_loop(monkeypatch):
    event_loop_thread = threading.get_ident()
    worker_threads = []

    def parse(_content):
        worker_threads.append(threading.get_ident())
        return "extracted study material " * 5

    monkeypatch.setattr(file_service, "_extract_from_pdf", parse)
    pdf_text, pdf_ocr = await file_service._extract_text(b"pdf", "pdf", "application/pdf")
    assert pdf_text.startswith("extracted study material")
    assert not pdf_ocr

    monkeypatch.setattr(file_service, "_extract_from_docx", parse)
    docx_text, docx_ocr = await file_service._extract_text(
        b"docx",
        "docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert docx_text.startswith("extracted study material")
    assert not docx_ocr
    assert len(worker_threads) == 2
    assert all(thread_id != event_loop_thread for thread_id in worker_threads)


@pytest.mark.asyncio
async def test_scanned_pdf_rendering_is_off_loop_and_bounded(monkeypatch):
    active = 0
    maximum_active = 0
    calls = 0
    worker_threads = []
    lock = threading.Lock()

    def page_count(_content):
        return 3

    def render(_content, _page_number):
        nonlocal active, maximum_active, calls
        with lock:
            active += 1
            calls += 1
            maximum_active = max(maximum_active, active)
            worker_threads.append(threading.get_ident())
        time.sleep(0.025)
        with lock:
            active -= 1
        return b"rendered-page"

    class FakeOCREngine:
        async def extract_from_image(self, _image_bytes):
            await asyncio.sleep(0)
            return "page text"

    monkeypatch.setattr(file_service, "_get_pdf_page_count", page_count)
    monkeypatch.setattr(file_service, "_render_pdf_page", render)
    monkeypatch.setattr(file_service, "get_ocr_engine", lambda: FakeOCREngine())

    event_loop_thread = threading.get_ident()
    ticked = asyncio.Event()
    async def observe_loop():
        await asyncio.sleep(0.005)
        ticked.set()

    jobs = [
        asyncio.create_task(file_service._ocr_pdf_pages(b"pdf"))
        for _ in range(3)
    ]
    await observe_loop()
    results = await asyncio.gather(*jobs)

    assert ticked.is_set()
    assert results == ["page text\npage text\npage text"] * 3
    assert calls == 9
    assert maximum_active <= file_service.MAX_CONCURRENT_PDF_OCR
    assert all(thread_id != event_loop_thread for thread_id in worker_threads)


@pytest.mark.asyncio
async def test_cancelling_scanned_pdf_waits_for_active_render(monkeypatch):
    finished = threading.Event()

    def render(_content, _page_number):
        time.sleep(0.05)
        finished.set()
        return b"rendered-page"

    class FakeOCREngine:
        async def extract_from_image(self, _image_bytes):
            return "page text"

    monkeypatch.setattr(file_service, "_get_pdf_page_count", lambda _content: 1)
    monkeypatch.setattr(file_service, "_render_pdf_page", render)
    monkeypatch.setattr(file_service, "get_ocr_engine", lambda: FakeOCREngine())

    task = asyncio.create_task(file_service._ocr_pdf_pages(b"pdf"))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert finished.is_set()


def test_scanned_pdf_page_pixel_budget_preserves_normal_scale():
    assert file_service._pdf_render_zoom(612, 792) == 2.0
    zoom = file_service._pdf_render_zoom(10_000, 10_000)
    assert zoom < 2.0
    assert 10_000 * 10_000 * zoom * zoom <= file_service.MAX_OCR_PAGE_PIXELS


def test_actual_pymupdf_raster_respects_pixel_cap():
    fitz = pytest.importorskip("fitz")
    document = fitz.open()
    document.new_page(width=4_000, height=4_000)
    content = document.tobytes()
    document.close()

    png = file_service._render_pdf_page(content, 0)
    width, height = struct.unpack(">II", png[16:24])

    assert width * height <= file_service.MAX_OCR_PAGE_PIXELS
