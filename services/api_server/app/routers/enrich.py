"""
Router: /api/v1/enrich — Data Enrichment & Full CRUD for Loan Records
"""
from datetime import date
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import StreamingResponse

from services.api_server.app.schemas.loan import EnrichPayload
from services.api_server.app.services import enrich as enrich_svc

router = APIRouter(prefix="/api/v1/enrich", tags=["Data Enrichment"])


@router.post("", summary="[C] Tạo mới hồ sơ khoản vay vào tập dữ liệu")
def save_enriched_record(payload: EnrichPayload):
    """
    Lưu một hồ sơ vay mới vào CSV (data/raw/enriched_loan_data_YYYYMMDD.csv).
    - Mỗi ngày một file; các hồ sơ trong ngày được APPEND.
    - loan_status=-1 nghĩa là chưa gán nhãn; sẽ cập nhật sau qua endpoint PATCH/PUT.
    """
    try:
        result = enrich_svc.save_record(payload)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lưu dữ liệu: {e}")


@router.get("/records", summary="[R] Lấy danh sách hồ sơ hàng đợi thẩm định (phân trang)")
def get_enriched_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str = Query("all", description="Nguồn dữ liệu: 'all', 'live', 'backlog'"),
    grade: Optional[str] = Query(None, description="Lọc theo grade (A-G)"),
    search: Optional[str] = Query(None, description="Tìm kiếm theo mã hồ sơ / client_ID"),
):
    """
    Truy vấn danh sách hồ sơ (Read) cho Hàng đợi Thẩm định.
    Hỗ trợ kết hợp cả luồng nộp trực tuyến (Live) và kho hồ sơ cần thẩm định thủ công (Backlog Grade C-D).
    """
    try:
        live_records = enrich_svc.read_all_records()
        active_backlog = enrich_svc.read_manual_review_backlog(limit=None)
        
        if source == "live":
            pool = live_records
        elif source == "backlog":
            pool = active_backlog
        else: # all
            pool = live_records + active_backlog

        # Lọc theo grade nếu có
        if grade and grade != "ALL":
            pool = [r for r in pool if str(r.get("loan_grade", "")).upper() == grade.upper()]

        # Lọc theo từ khóa tìm kiếm nếu có
        if search:
            s = search.lower().strip()
            pool = [
                r for r in pool
                if s in str(r.get("client_ID", "")).lower()
                or s in str(r.get("application_id", "")).lower()
                or s in str(r.get("loan_intent", "")).lower()
            ]

        total = len(pool)
        start = (page - 1) * page_size
        paginated_records = pool[start: start + page_size]

        return {
            "success":       True,
            "total":         total,
            "page":          page,
            "page_size":     page_size,
            "total_pages":   (total + page_size - 1) // page_size if total > 0 else 0,
            "records":       paginated_records,
            "live_count":    len(live_records),
            "backlog_count": len(active_backlog),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi đọc dữ liệu: {e}")


@router.get("/records/{client_id}", summary="[R] Xem chi tiết một hồ sơ khoản vay")
def get_single_record(client_id: str):
    """Lấy chi tiết đầy đủ của một hồ sơ theo client_ID hoặc application_id."""
    record = enrich_svc.get_record_by_id(client_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ: {client_id}")
    return {"success": True, "record": record}


@router.put("/records/{client_id}", summary="[U] Cập nhật / Điều chỉnh thông tin khoản vay")
def update_loan_record(client_id: str, updates: Dict[str, Any] = Body(...)):
    """
    Cập nhật các thuộc tính khoản vay (Số tiền vay, kỳ hạn, lãi suất, phân hạng, mục đích, nhãn phê duyệt).
    """
    try:
        updated = enrich_svc.update_record_details(client_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Không tìm thấy hồ sơ để cập nhật: {client_id}")
        return {"success": True, "record": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật hồ sơ: {e}")


@router.patch("/records/{client_id}/label", summary="[U] Gán nhãn / Phê duyệt nhanh hồ sơ")
def label_enriched_record(client_id: str, loan_status: int = 0):
    """
    Cập nhật quyết định thẩm định cho một hồ sơ (cả hồ sơ Live và Backlog).
    loan_status: 0 = Phê duyệt (Trả nợ tốt) | 1 = Từ chối (Nợ xấu)
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
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật thẩm định: {e}")


@router.delete("/records/{client_id}", summary="[D] Xóa hồ sơ khoản vay khỏi hàng đợi")
def delete_loan_record(client_id: str):
    """
    Xóa một hồ sơ khoản vay khỏi hệ thống.
    """
    try:
        success = enrich_svc.delete_record(client_id)
        return {"success": success, "client_ID": client_id, "message": "Đã xóa hồ sơ thành công."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xóa hồ sơ: {e}")


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
