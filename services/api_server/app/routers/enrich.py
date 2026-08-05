"""
Router: /api/v1/enrich — Data Enrichment (lưu, đọc, gán nhãn, export)
"""
from datetime import date
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from services.api_server.app.schemas.loan import EnrichPayload
from services.api_server.app.services import enrich as enrich_svc

router = APIRouter(prefix="/api/v1/enrich", tags=["Data Enrichment"])


@router.post("", summary="Lưu hồ sơ vào tập dữ liệu")
def save_enriched_record(payload: EnrichPayload):
    """
    Lưu một hồ sơ vay vào file CSV (data/raw/enriched_loan_data_YYYYMMDD.csv).
    - Mỗi ngày một file; các hồ sơ trong ngày được APPEND.
    - loan_status=-1 nghĩa là chưa gán nhãn; sẽ cập nhật sau qua endpoint PATCH.
    """
    try:
        result = enrich_svc.save_record(payload)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lưu dữ liệu: {e}")


@router.get("/records", summary="Lấy danh sách hồ sơ đã lưu (phân trang)")
def get_enriched_records(page: int = 1, page_size: int = 20):
    """Trả về danh sách hồ sơ enriched, sắp xếp mới nhất trước, có phân trang."""
    try:
        all_records = enrich_svc.read_all_records()
        total = len(all_records)
        start = (page - 1) * page_size
        return {
            "success":     True,
            "total":       total,
            "page":        page,
            "page_size":   page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
            "records":     all_records[start: start + page_size],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc dữ liệu: {e}")


@router.get("/stats", summary="Thống kê tập dữ liệu enriched")
def get_enrich_stats():
    """Trả về thống kê: tổng hồ sơ, phân bố nhãn, default rate, tiến độ re-train."""
    try:
        all_records = enrich_svc.read_all_records()
        return {"success": True, **enrich_svc.build_stats(all_records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tính thống kê: {e}")


@router.get("/export", summary="Export toàn bộ dữ liệu enriched ra CSV")
def export_enriched_data():
    """Stream toàn bộ dữ liệu enriched về dưới dạng file CSV."""
    try:
        all_records = enrich_svc.read_all_records()
        if not all_records:
            raise HTTPException(status_code=404, detail="Chưa có dữ liệu để export.")

        output = enrich_svc.export_csv(all_records)
        filename = f"enriched_dataset_{date.today().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi export: {e}")


@router.patch("/records/{client_id}/label", summary="Gán/cập nhật nhãn thực tế cho hồ sơ")
def label_enriched_record(client_id: str, loan_status: int = 0):
    """
    Cập nhật trường loan_status (Ground Truth) cho một hồ sơ đã lưu.
    loan_status: 0 = Trả nợ tốt | 1 = Nợ xấu
    """
    if loan_status not in (0, 1):
        raise HTTPException(status_code=400, detail="loan_status phải là 0 hoặc 1")
    try:
        found = enrich_svc.update_label(client_id, loan_status)
        if not found:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ: {client_id}")
        return {"success": True, "client_ID": client_id, "loan_status": loan_status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật nhãn: {e}")
